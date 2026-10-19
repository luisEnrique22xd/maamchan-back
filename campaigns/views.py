from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Q, Count
from django.utils import timezone

from .models import Campaign, TargetByTeam, LevelConfig
from sales.models import Sale

class ActiveCampaignProjectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        campaign = Campaign.objects.filter(is_active=True, start_date__lte=today, end_date__gte=today).first()

        if not campaign:
            return Response({"message": "No hay ninguna campaña activa programada para hoy."}, status=404)

        sales_in_campaign = Sale.objects.filter(
            created_at__date__gte=campaign.start_date,
            created_at__date__lte=campaign.end_date,
            status='PAGADO' # O ventas válidas
        )

        total_real_sales = sales_in_campaign.aggregate(total=Sum('total_amount'))['total'] or 0
        total_real_orders = sales_in_campaign.count()
        progress_percentage = min(round((total_real_sales / campaign.global_target) * 100, 1), 100) if campaign.global_target > 0 else 0

        team_targets = TargetByTeam.objects.filter(campaign=campaign).select_related('coordinator')
        teams_progress = []

        levels = LevelConfig.objects.all().order_by('required_orders')

        for item in team_targets:
            coord = item.coordinator
            vendedoras_ids = coord.vendedoras_a_cargo.values_list('id', flat=True) if hasattr(coord, 'vendedoras_a_cargo') else []
            
            coord_sales_qs = sales_in_campaign.filter(
                Q(seller=coord) | Q(seller_id__in=vendedoras_ids)
            )
            
            coord_sales = coord_sales_qs.aggregate(total=Sum('total_amount'))['total'] or 0
            coord_orders = coord_sales_qs.count()

            team_pct = min(round((coord_sales / item.target_amount) * 100, 1), 100) if item.target_amount > 0 else 0

            # Determinar nivel actual según la tabla de pedidos
            current_level = "Sin Nivel"
            earnings_order_rate = 0
            est_cash = 0
            est_product = 0

            for lvl in levels:
                if coord_orders >= lvl.required_orders:
                    current_level = lvl.get_name_display()
                    earnings_order_rate = float(lvl.earnings_per_order)
                    est_cash = float(lvl.cash_bonus)
                    est_product = float(lvl.free_product_bonus)

            teams_progress.append({
                "coordinator_id": coord.id,
                "coordinator_name": coord.full_name,
                "target_amount": float(item.target_amount),
                "achieved_amount": float(coord_sales),
                "target_orders": item.target_orders,
                "achieved_orders": coord_orders,
                "percentage": team_pct,
                "current_level": current_level,
                "estimated_cash_bonus": est_cash,
                "estimated_free_product": est_product,
                "remaining_amount": max(float(item.target_amount) - float(coord_sales), 0)
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
                "total_real_orders": total_real_orders,
                "progress_percentage": progress_percentage,
            },
            "teams_progress": teams_progress
        })