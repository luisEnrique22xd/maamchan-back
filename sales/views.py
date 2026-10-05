from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import transaction

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
        queryset = Sale.objects.all()

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
            # Re-obtener la venta para reflejar los totales actualizados por el método save() del modelo Payment
            sale.refresh_from_db()

        return response