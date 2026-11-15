import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Campaign, TargetByTeam, LevelConfig
from sales.models import Sale

class ActiveCampaignProjectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            today = timezone.now().date()
            campaign = Campaign.objects.filter(is_active=True).order_by('-start_date').first()

            if not campaign:
                return Response({"message": "No hay ninguna campaña activa programada."}, status=404)

            start_date = campaign.start_date or today
            end_date = campaign.end_date or today
            total_days = max(1, (end_date - start_date).days + 1)
            current_day = max(1, min((today - start_date).days, total_days))
            sales_in_campaign = Sale.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )

            total_real_sales = sales_in_campaign.aggregate(total=Sum('total_amount'))['total'] or 0
            total_real_orders = sales_in_campaign.count()
            
            global_target = float(campaign.global_target) if campaign.global_target else 0
            progress_percentage = min(round((float(total_real_sales) / global_target) * 100, 1), 100) if global_target > 0 else 0

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

                team_pct = min(round((float(coord_sales) / float(item.target_amount)) * 100, 1), 100) if item.target_amount > 0 else 0

                current_level = "Sin Nivel"
                est_cash = 0
                est_product = 0

                for lvl in levels:
                    if coord_orders >= lvl.required_orders:
                        current_level = lvl.get_name_display()
                        est_cash = float(lvl.cash_bonus)
                        est_product = float(lvl.free_product_bonus)

                teams_progress.append({
                    "coordinator_id": coord.id,
                    "coordinator_name": getattr(coord, 'full_name', str(coord)),
                    "target_amount": float(item.target_amount),
                    "achieved_amount": float(coord_sales),
                    "target_orders": item.target_orders,
                    "achieved_orders": coord_orders,
                    "percentage": team_pct,
                    "current_level": current_level,
                    "estimated_cash_bonus": est_cash,
                    "estimated_free_product": est_product,
                })

            return Response({
                "campaign": {
                    "id": campaign.id,
                    "code": campaign.code,
                    "name": campaign.name,
                    "start_date": campaign.start_date,
                    "end_date": campaign.end_date,
                    "global_target": global_target,
                    "total_real_sales": float(total_real_sales),
                    "total_real_orders": total_real_orders,
                    "progress_percentage": progress_percentage,
                    "current_day": current_day,
                    "total_days": total_days,
                    "goal_orders": 30,
                    "current_orders": total_real_orders,
                    "new_clients_pct": 50,
                    "reactivations_pct": 30,
                    "resort_pct": 20
                },
                "teams_progress": teams_progress
            })
        except Exception as e:
            # ESTO DEVOLVERÁ EL ERROR EXACTO EN LA CONSOLA DEL NAVEGADOR
            error_trace = traceback.format_exc()
            print("--- ERROR 500 DETALLADO ---")
            print(error_trace)
            return Response({"error": str(e), "trace": error_trace}, status=500)