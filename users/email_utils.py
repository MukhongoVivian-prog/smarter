# users/email_utils.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
import logging
import os

logger = logging.getLogger(__name__)
User = get_user_model()

class EmailService:
    """Enhanced email service with template support and comprehensive functionality"""
    
    @staticmethod
    def _send_templated_email(recipient_email, subject, template_name, context, recipient_name=None):
        """
        Send templated email with both HTML and plain text versions
        
        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            template_name: Template name (without .html extension)
            context: Template context dictionary
            recipient_name: Optional recipient name for logging
        """
        try:
            # Add default context
            default_context = {
                'site_name': 'SmartHunt',
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:3000'),
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@smarthunt.com'),
                'timestamp': timezone.now()
            }
            context.update(default_context)
            
            # Render HTML template
            html_content = render_to_string(f'emails/{template_name}.html', context)
            
            # Create plain text version by stripping HTML (basic implementation)
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content.strip())
            
            # Create email message
            msg = EmailMultiAlternatives(
                subject=f"{getattr(settings, 'EMAIL_SUBJECT_PREFIX', '[SmartHunt] ')}{subject}",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send()
            
            logger.info(f"Templated email '{template_name}' sent to {recipient_email} ({recipient_name or 'Unknown'})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send templated email '{template_name}' to {recipient_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email using template"""
        context = {
            'user': user,
        }
        
        return EmailService._send_templated_email(
            recipient_email=user.email,
            subject="Welcome to SmartHunt!",
            template_name="welcome",
            context=context,
            recipient_name=user.get_full_name() or user.username
        )
    
    @staticmethod
    def send_booking_notification_email(booking_request, notification_type='created'):
        """Send booking notification email using template"""
        try:
            # Determine recipient based on notification type
            if notification_type == 'created':
                recipient = booking_request.property.owner
            else:
                recipient = booking_request.tenant
            
            # Prepare context
            context = {
                'booking': booking_request,
                'recipient': recipient,
                'notification_type': notification_type,
                'property': booking_request.property,
                'tenant': booking_request.tenant,
                'landlord': booking_request.property.owner
            }
            
            # Determine subject based on notification type
            subjects = {
                'created': f"New Booking Request for {booking_request.property.title}",
                'approved': "Great News! Your Booking Request was Approved",
                'declined': "Booking Request Update",
                'checked_in': "Tenant Has Checked In",
                'completed': "Booking Completed Successfully",
                'cancelled': "Booking Cancelled"
            }
            
            subject = subjects.get(notification_type, "Booking Update")
            
            return EmailService._send_templated_email(
                recipient_email=recipient.email,
                subject=subject,
                template_name="booking_notification",
                context=context,
                recipient_name=recipient.get_full_name() or recipient.username
            )
            
        except Exception as e:
            logger.error(f"Failed to send booking notification email: {str(e)}")
            return False
    
    @staticmethod
    def send_maintenance_notification_email(maintenance_request, notification_type='created'):
        """Send maintenance notification email using template"""
        try:
            # Determine recipient based on notification type
            if notification_type == 'created':
                recipient = maintenance_request.property.owner
            else:
                recipient = maintenance_request.tenant
            
            # Prepare context
            context = {
                'maintenance': maintenance_request,
                'recipient': recipient,
                'notification_type': notification_type,
                'property': maintenance_request.property,
                'tenant': maintenance_request.tenant,
                'landlord': maintenance_request.property.owner
            }
            
            # Determine subject based on notification type
            subjects = {
                'created': f"New Maintenance Request for {maintenance_request.property.title}",
                'in_progress': "Maintenance Request In Progress",
                'resolved': "Maintenance Request Resolved",
                'cancelled': "Maintenance Request Cancelled"
            }
            
            subject = subjects.get(notification_type, "Maintenance Update")
            
            return EmailService._send_templated_email(
                recipient_email=recipient.email,
                subject=subject,
                template_name="maintenance_notification",
                context=context,
                recipient_name=recipient.get_full_name() or recipient.username
            )
            
        except Exception as e:
            logger.error(f"Failed to send maintenance notification email: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user, reset_link, request_ip=None):
        """Send password reset email using template"""
        context = {
            'user': user,
            'reset_link': reset_link,
            'request_ip': request_ip,
        }
        
        return EmailService._send_templated_email(
            recipient_email=user.email,
            subject="Password Reset Request",
            template_name="password_reset",
            context=context,
            recipient_name=user.get_full_name() or user.username
        )

# Backward compatibility - keep original function names
def send_welcome_email(user):
    """Backward compatibility wrapper"""
    return EmailService.send_welcome_email(user)

def send_booking_notification_email(booking_request, notification_type='created'):
    """Backward compatibility wrapper"""
    return EmailService.send_booking_notification_email(booking_request, notification_type)

def send_maintenance_notification_email(maintenance_request, notification_type='created'):
    """Backward compatibility wrapper"""
    return EmailService.send_maintenance_notification_email(maintenance_request, notification_type)

def send_password_reset_email(user, reset_link, request_ip=None):
    """Backward compatibility wrapper"""
    return EmailService.send_password_reset_email(user, reset_link, request_ip)

def send_welcome_email(user):
    """Send welcome email to new users"""
    try:
        subject = f'{settings.EMAIL_SUBJECT_PREFIX}Welcome to SmartHunt!'
        
        context = {
            'user': user,
            'site_name': 'SmartHunt',
        }
        
        # Plain text version
        text_content = f"""
        Welcome to SmartHunt, {user.first_name or user.username}!
        
        Thank you for joining our property rental platform. You can now:
        - Browse available properties
        - Save favorites
        - Contact landlords
        - Submit booking requests
        
        Get started by exploring properties in your area.
        
        Best regards,
        The SmartHunt Team
        """
        
        # HTML version (you can create templates later)
        html_content = f"""
        <h2>Welcome to SmartHunt, {user.first_name or user.username}!</h2>
        <p>Thank you for joining our property rental platform.</p>
        <p>You can now:</p>
        <ul>
            <li>Browse available properties</li>
            <li>Save favorites</li>
            <li>Contact landlords</li>
            <li>Submit booking requests</li>
        </ul>
        <p>Get started by exploring properties in your area.</p>
        <p>Best regards,<br>The SmartHunt Team</p>
        """
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_booking_notification_email(booking_request, notification_type='created'):
    """Send email notifications for booking requests"""
    try:
        if notification_type == 'created':
            # Notify landlord of new booking request
            recipient = booking_request.property.owner
            subject = f'{settings.EMAIL_SUBJECT_PREFIX}New Booking Request for {booking_request.property.title}'
            
            text_content = f"""
            Hello {recipient.first_name or recipient.username},
            
            You have received a new booking request for your property "{booking_request.property.title}".
            
            Tenant: {booking_request.tenant.username}
            Property: {booking_request.property.title}
            Location: {booking_request.property.location}
            Message: {booking_request.message or 'No message provided'}
            
            Please log in to your dashboard to review and respond to this request.
            
            Best regards,
            The SmartHunt Team
            """
            
        elif notification_type in ['approved', 'declined']:
            # Notify tenant of booking status update
            recipient = booking_request.tenant
            status_text = 'approved' if notification_type == 'approved' else 'declined'
            subject = f'{settings.EMAIL_SUBJECT_PREFIX}Booking Request {status_text.title()}'
            
            text_content = f"""
            Hello {recipient.first_name or recipient.username},
            
            Your booking request for "{booking_request.property.title}" has been {status_text}.
            
            Property: {booking_request.property.title}
            Location: {booking_request.property.location}
            Status: {status_text.title()}
            
            {'Congratulations! Please contact the landlord to arrange next steps.' if notification_type == 'approved' else 'Thank you for your interest. Feel free to explore other properties.'}
            
            Best regards,
            The SmartHunt Team
            """
        else:
            return False
        
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
        )
        
        logger.info(f"Booking notification email sent to {recipient.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send booking notification email: {str(e)}")
        return False

def send_maintenance_notification_email(maintenance_request, notification_type='created'):
    """Send email notifications for maintenance requests"""
    try:
        if notification_type == 'created':
            # Notify landlord of new maintenance request
            recipient = maintenance_request.property.owner
            subject = f'{settings.EMAIL_SUBJECT_PREFIX}New Maintenance Request for {maintenance_request.property.title}'
            
            text_content = f"""
            Hello {recipient.first_name or recipient.username},
            
            A maintenance request has been submitted for your property "{maintenance_request.property.title}".
            
            Tenant: {maintenance_request.tenant.username}
            Property: {maintenance_request.property.title}
            Description: {maintenance_request.description}
            Status: {maintenance_request.status}
            
            Please log in to your dashboard to review and respond to this request.
            
            Best regards,
            The SmartHunt Team
            """
            
        elif notification_type in ['in_progress', 'resolved']:
            # Notify tenant of maintenance status update
            recipient = maintenance_request.tenant
            status_text = maintenance_request.get_status_display()
            subject = f'{settings.EMAIL_SUBJECT_PREFIX}Maintenance Request Update'
            
            text_content = f"""
            Hello {recipient.first_name or recipient.username},
            
            Your maintenance request for "{maintenance_request.property.title}" has been updated.
            
            Property: {maintenance_request.property.title}
            Description: {maintenance_request.description}
            New Status: {status_text}
            
            Thank you for your patience.
            
            Best regards,
            The SmartHunt Team
            """
        else:
            return False
        
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
        )
        
        logger.info(f"Maintenance notification email sent to {recipient.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send maintenance notification email: {str(e)}")
        return False

def send_password_reset_email(user, reset_link):
    """Send password reset email"""
    try:
        subject = f'{settings.EMAIL_SUBJECT_PREFIX}Password Reset Request'
        
        text_content = f"""
        Hello {user.first_name or user.username},
        
        You have requested to reset your password for your SmartHunt account.
        
        Click the link below to reset your password:
        {reset_link}
        
        If you did not request this password reset, please ignore this email.
        
        Best regards,
        The SmartHunt Team
        """
        
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False
