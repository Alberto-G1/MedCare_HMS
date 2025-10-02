from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

def index_view(request):
    return render(request, 'public/index.html')

def features_view(request):
    return render(request, 'public/features.html')

def about_view(request):
    return render(request, 'public/about.html')

def team_view(request):
    return render(request, 'public/team.html')

def team_detail_view(request):
    return render(request, 'public/team-detail.html')

def message_test_view(request):
    """Test page for the enhanced message system"""
    return render(request, 'message_test.html')


def contact_view(request):
    if request.method == 'POST':
        # Get the form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message_body = request.POST.get('message')

        # Basic validation: ensure required fields are not empty
        if not all([name, email, subject, message_body]):
            messages.error(request, 'Please fill out all the fields in the form.')
            return render(request, 'public/contact.html')

        # Construct the email content
        full_subject = f"MedCare HMS Contact Form: {subject}"
        full_message = f"""
        You have received a new message from your website's contact form.

        Name: {name}
        Email: {email}
        --------------------------------------------------

        Message:
        {message_body}
        """

        # The list of recipient emails
        recipient_list = [
            'okwiiyakub@gmail.com',
            'annetkatushabe891@gmail.com',
            'nuwarindaalbertgrande@gmail.com',
            'wkatswamba@gmail.com',
        ]

        try:
            # Send the email
            send_mail(
                subject=full_subject,
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully! We will get back to you shortly.')
            return redirect('contact') # Redirect to the same page to clear the form
        
        except Exception as e:
            # Handle potential errors (e.g., wrong password, network issues)
            messages.error(request, f'Sorry, there was an error sending your message. Please try again later. Error: {e}')

    return render(request, 'public/contact.html')