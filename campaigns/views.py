from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Q
from django.utils import timezone

from .models import Campaign, TargetByTeam
from sales.models import Sale

class ActiveCampaignProjectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        # Obtener la campaña activa actual
        campaign = Campaign.objects.filter(is_active=True, start_date__lte=today, end_date__gte=today).first()

        if not campaign:
            return Response({"message": "No hay ninguna campaña activa programada para hoy."}, status=404)

        # Ventas reales logradas durante las fechas de la campaña
        sales_in_campaign = Sale.objects.filter(
            created_at__date__gte=campaign.start_date,
            created_at__date__lte=campaign.end_date
        )

        total_real_sales = sales_in_campaign.aggregate(total=Sum('total_amount'))['total'] or 0
        progress_percentage = min(round((total_real_sales / campaign.global_target) * 100, 1), 100) if campaign.global_target > 0 else 0

        # Desglose por Equipos / Coordinadoras
        team_targets = TargetByTeam.objects.filter(campaign=campaign).select_related('coordinator')
        teams_progress = []

        for item in team_targets:
            coord = item.coordinator
            # Ajuste de relación según CustomUser: vendedoras_a_cargo
            vendedoras_ids = coord.vendedoras_a_cargo.values_list('id', flat=True) if hasattr(coord, 'vendedoras_a_cargo') else []
            
            coord_sales = sales_in_campaign.filter(
                Q(seller=coord) | Q(seller_id__in=vendedoras_ids)
            ).aggregate(total=Sum('total_amount'))['total'] or 0

            team_pct = min(round((coord_sales / item.target_amount) * 100, 1), 100) if item.target_amount > 0 else 0

            teams_progress.append({
                "coordinator_id": coord.id,
                "coordinator_name": coord.full_name,
                "target": float(item.target_amount),
                "achieved": float(coord_sales),
                "percentage": team_pct,
                "remaining": max(float(item.target_amount) - float(coord_sales), 0)
            })

        return Response({
            "campaign": {
                "id": campaign.id,
                "code": campaign.code,
                "name": campaign.name,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "global_target": float(campaign.global_target),
                "total_real_sales": float(total_real_sales),
                "progress_percentage": progress_percentage,
            },
            "teams_progress": teams_progress
        })