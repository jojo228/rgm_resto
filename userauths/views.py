from django.shortcuts import redirect, render
from userauths.forms import UserRegisterForm, ProfileForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.conf import settings
from userauths.models import Profile, User
from django.utils import timezone
from django.core.mail import send_mail  # For email OTP


# User = settings.AUTH_USER_MODEL


import random
from django.core.mail import send_mail
from django.conf import settings

def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST or None)
        if form.is_valid():
            new_user = form.save()
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get("email")
            messages.success(
                request, f"Hey {username}, your account was created successfully. An OTP has been sent to your email."
            )
            
            # Generate a random OTP
            otp = random.randint(100000, 999999)

            # Save OTP to the session (or a temporary model if you prefer)
            request.session['otp'] = otp
            request.session['email'] = email

            # Send OTP email
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}.',
                'togotulawo@gmail.com',
                [email],
                fail_silently=False,
            )

            # Redirect to the OTP verification page
            return redirect('userauths:verify_otp')

    else:
        form = UserRegisterForm()

    context = {
        "form": form,
    }
    return render(request, "sign-up.html", context)




# views.py

def verify_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")
        email = request.POST.get("email")  # Get the email from the request

        # Here you should verify the OTP (this can vary depending on your implementation)
        if verify_otp(otp, email):  # Implement this function to check OTP
            user = User.objects.get(email=email)  # Fetch the user based on email
            user.is_active = True  # Activate the user
            user.save()  # Save the user
            
            login(request, user)  # Log the user in
            messages.success(request, "Your account has been activated successfully!")
            return redirect("userauths:sign-in")  # Redirect to the login page or any other page
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "verify_otp.html")





def login_view(request):
    if request.user.is_authenticated:
        messages.warning(request, f"Hey you are already Logged In.")
        return redirect("core:index")

    if request.method == "POST":
        email = request.POST.get("email")  # peanuts@gmail.com
        password = request.POST.get("password")  # getmepeanuts

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "You are logged in.")
                return redirect("core:index")
            else:
                messages.warning(request, "User Does Not Exist, create an account.")

        except:
            messages.warning(request, f"User with {email} does not exist")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You logged out.")
    return redirect("userauths:sign-in")


def profile_update(request):
    profile = Profile.objects.get(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            new_form = form.save(commit=False)
            new_form.user = request.user
            new_form.save()
            messages.success(request, "Profile Updated Successfully.")
            return redirect("userauths:profile-update")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
    }

    return render(request, "dashboard-edit-profile.html", context)
