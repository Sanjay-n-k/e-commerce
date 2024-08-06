from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Order
import razorpay
from django.conf import settings
import json
from django.shortcuts import render, redirect, get_object_or_404
import logging
from .forms import CustomUserCreationForm


# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})

@login_required
def product_detail(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        phone_number = request.POST.get('phone_number')
        order = Order(product=product, user=request.user, quantity=quantity, phone_number=phone_number)
        order.save()
        return redirect('order_confirmation')
    return render(request, 'shop/product_detail.html', {'product': product})

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('product_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'shop/signup.html', {'form': form})

@login_required
def order_confirmation(request):
    return render(request, 'shop/order_confirmation.html')

def custom_logout(request):
    logout(request)
    return redirect('login')  # Redirect to the login page after logout

logger = logging.getLogger(__name__)

@csrf_exempt
def buy_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity'))
            phone_number = data.get('phone_number')
            amount = int(product.price * quantity * 100 ) # Convert amount to paise

            # Create an order with Razorpay
            order = client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': '1'
            })
            order_id = order['id']

            # Save order to database
            Order.objects.create(
                product=product,
                user=request.user,
                quantity=quantity,
                phone_number=phone_number,
                order_id=order_id
            )

            return JsonResponse({'order_id': order_id, 'amount': amount, 'currency': 'INR'})
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'shop/buy_product.html', {'product': product})

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_id = data.get('razorpay_payment_id')
            order_id = data.get('razorpay_order_id')
            signature = data.get('razorpay_signature')

            # Verify the payment signature
            order = get_object_or_404(Order, order_id=order_id)
            generated_signature = client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            })

            if generated_signature:
                # Payment is verified
                order.payment_id = payment_id
                order.signature = signature
                order.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'failure'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)