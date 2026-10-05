from django.db import transaction
from rest_framework import serializers
from .models import Category, Product, Sale, SaleItem, Payment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = Product
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        # read_only_fields = ['sale']


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')

    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']


class CreateSaleItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Payment.PaymentMethod.choices, default=Payment.PaymentMethod.EFECTIVO)
    reference = serializers.CharField(required=False, allow_blank=True)


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    seller_name = serializers.ReadOnlyField(source='seller.full_name')

    # Campos de entrada solo para escritura al procesar Checkout
    input_items = CreateSaleItemSerializer(many=True, write_only=True)
    initial_payment = CreatePaymentSerializer(required=False, write_only=True)

    class Meta:
        model = Sale
        fields = [
            'id', 'seller', 'seller_name', 'customer_name', 'sale_type',
            'status', 'total_amount', 'paid_amount', 'balance_due',
            'items', 'payments', 'input_items', 'initial_payment', 'created_at'
        ]
        read_only_fields = ['seller', 'status', 'total_amount', 'paid_amount', 'balance_due', 'created_at']

    def create(self, validated_data):
        input_items = validated_data.pop('input_items')
        initial_payment = validated_data.pop('initial_payment', None)

        with transaction.atomic():
            # 1. Crear la venta
            sale = Sale.objects.create(**validated_data)
            total_sale = 0

            # 2. Procesar cada producto y descontar inventario
            for item_data in input_items:
                try:
                    product = Product.objects.get(id=item_data['product_id'], is_active=True)
                except Product.DoesNotExist:
                    raise serializers.ValidationError(f"El producto con ID {item_data['product_id']} no existe o está inactivo.")

                if product.stock < item_data['quantity']:
                    raise serializers.ValidationError(f"Stock insuficiente para '{product.name}'. Disponible: {product.stock}")

                # Descontar stock
                product.stock -= item_data['quantity']
                product.save()

                # Crear renglón de la venta
                subtotal = item_data['unit_price'] * item_data['quantity']
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    subtotal=subtotal
                )
                total_sale += subtotal

            sale.total_amount = total_sale

            # 3. Registrar el pago inicial si se incluyó
            if initial_payment and initial_payment.get('amount', 0) > 0:
                paid_amount = initial_payment['amount']
                Payment.objects.create(
                    sale=sale,
                    amount=paid_amount,
                    payment_method=initial_payment.get('payment_method', Payment.PaymentMethod.EFECTIVO),
                    reference=initial_payment.get('reference', '')
                )
                sale.paid_amount = paid_amount

            # 4. Actualizar saldo y estado
            sale.balance_due = sale.total_amount - sale.paid_amount
            if sale.balance_due <= 0 and sale.total_amount > 0:
                sale.status = Sale.Status.PAGADO
            else:
                sale.status = Sale.Status.PENDIENTE

            sale.save()
            return sale