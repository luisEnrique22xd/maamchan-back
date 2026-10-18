from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q

from .models import Category, Product, Sale, Payment
from .serializers import CategorySerializer, ProductSerializer, SaleSerializer, PaymentSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user

        # 0. FILTRADO JERÁRQUICO POR RED DE VENTAS
        if user.is_superuser or user.role_primary == 'DIRECTORA':
            # La Directora ve absolutamente todas las ventas de la red
            queryset = Sale.objects.select_related('seller', 'seller__coordinadora').all()
        elif user.role_primary == 'COORDINADORA':
            # La Coordinadora ve sus propias ventas + las de sus vendedoras a cargo
            equipo_ids = user.vendedoras_a_cargo.values_list('id', flat=True)
            queryset = Sale.objects.filter(
                Q(seller=user) | Q(seller_id__in=equipo_ids)
            ).select_related('seller', 'seller__coordinadora')
        else:
            # La Vendedora común solo ve sus propias ventas
            queryset = Sale.objects.filter(seller=user).select_related('seller', 'seller__coordinadora')

        # 1. Filtro por estado (PENDIENTE, PAGADO, CANCELADO)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())

        # 2. Filtro por tipo de venta (CONTADO, CREDITO, ANTICIPO)
        sale_type = self.request.query_params.get('sale_type')
        if sale_type:
            queryset = queryset.filter(sale_type=sale_type.upper())

        # 3. Búsqueda por nombre de cliente (búsqueda parcial insensible a mayúsculas)
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer_name__icontains=customer)

        # 4. Rango de fechas (formato: YYYY-MM-DD)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        sale_id = request.data.get('sale')
        amount = request.data.get('amount')

        if not sale_id or not amount:
            return Response(
                {"error": "Se requiere el ID de la venta ('sale') y el monto ('amount')."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response({"error": "La venta especificada no existe."}, status=status.HTTP_404_NOT_FOUND)

        if sale.status == Sale.Status.PAGADO:
            return Response({"error": "Esta venta ya se encuentra pagada completamente."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            response = super().create(request, *args, **kwargs)
            sale.refresh_from_db()

        return response
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Count, Q
from django.utils import timezone
from sales.models import Sale
from users.models import CustomUser

class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # Base QuerySet según la jerarquía del usuario
        if user.is_superuser or user.role_primary == 'DIRECTORA':
            sales_qs = Sale.objects.all()
            sellers_qs = CustomUser.objects.filter(role_primary='VENDEDORA', is_active=True)
        elif user.role_primary == 'COORDINADORA':
            equipo_ids = user.vendedoras_a_cargo.values_list('id', flat=True)
            sales_qs = Sale.objects.filter(Q(seller=user) | Q(seller_id__in=equipo_ids))
            sellers_qs = user.vendedoras_a_cargo.filter(is_active=True)
        else:
            sales_qs = Sale.objects.filter(seller=user)
            sellers_qs = CustomUser.objects.filter(id=user.id)

        # 1. Ventas del Mes
        sales_this_month = sales_qs.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        # 2. Cuentas por Cobrar (Saldos pendientes en ventas no pagadas)
        accounts_receivable = sales_qs.filter(
            status=Sale.Status.PENDIENTE
        ).aggregate(
            total_balance=Sum('balance_due'),
            count=Count('id')
        )

        # 3. Expedientes por Validar (Usuarios con estado pendiente, o ajusta según tu modelo de Expedientes)
        pending_expedientes = CustomUser.objects.filter(
            is_active=False # O un campo estado='PENDIENTE' si lo manejas en expediente
        ).count()

        # 4. Vendedoras Activas
        active_sellers = sellers_qs.count()

        # 5. Top 5 Líderes de Ventas
        top_sellers_data = sales_qs.filter(
            created_at__year=now.year,
            created_at__month=now.month
        ).values('seller__first_name', 'seller__last_name_paternal', 'seller__coordinadora__first_name')\
         .annotate(total_sales=Sum('total_amount'))\
         .order_by('-total_sales')[:5]

        top_sellers = [
            {
                "name": f"{item['seller__first_name']} {item['seller__last_name_paternal'] or ''}".strip(),
                "team": item['seller__coordinadora__first_name'] or "Directa",
                "sales": f"${item['total_sales']:,.2f}"
            }
            for item in top_sellers_data
        ]

        return Response({
            "user": {
                "first_name": user.first_name,
                "role_display": user.get_role_primary_display(),
            },
            "kpis": {
                "monthly_sales": f"${sales_this_month:,.2f}",
                "accounts_receivable_total": f"${accounts_receivable['total_balance'] or 0:,.2f}",
                "accounts_receivable_count": f"{accounts_receivable['count']} cuentas",
                "pending_expedientes": pending_expedientes,
                "active_sellers": active_sellers,
            },
            "top_sellers": top_sellers
        })