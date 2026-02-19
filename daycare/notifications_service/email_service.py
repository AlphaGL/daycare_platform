"""
Email Notification Service for Sugamama sugababies Daycare
Handles all transactional emails via Brevo SMTP
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_notification_email(to_email, subject, text_body, html_body=None):
    """
    Core email sender - wraps Django's send_mail with error handling.
    Returns True on success, False on failure.
    """
    try:
        if html_body:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=f"{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>",
                to=[to_email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()
        else:
            send_mail(
                subject=subject,
                message=text_body,
                from_email=f"{settings.DEFAULT_FROM_NAME} <{settings.DEFAULT_FROM_EMAIL}>",
                recipient_list=[to_email],
                fail_silently=False,
            )
        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# ─────────────────────────────────────────────
# ACCOUNT CREATION EMAILS
# ─────────────────────────────────────────────

def send_parent_welcome_email(user):
    """Send welcome email to a newly registered parent."""
    subject = f"Welcome to {settings.SITE_NAME}! 🎉"
    text_body = f"""
Hi {user.get_full_name()},

Welcome to {settings.SITE_NAME}! Your parent account has been created successfully.

Your Account Details:
  Username: {user.username}
  Email: {user.email}
  Role: Parent/Guardian

You can now:
  • Check your children in and out of daycare
  • View attendance records
  • Update your profile and check-in code

Log in here: {settings.SITE_URL}/accounts/login/

If you have any questions, please contact us.

Warm regards,
The {settings.SITE_NAME} Team
    """.strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
  <div style="background: #4CAF50; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0;">Welcome to {settings.SITE_NAME}! 🎉</h1>
  </div>
  <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>Hi <strong>{user.get_full_name()}</strong>,</p>
    <p>Your parent account has been created successfully. Here are your details:</p>
    <table style="background: white; padding: 16px; border-radius: 6px; width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 6px; color: #888;">Username</td><td style="padding: 6px;"><strong>{user.username}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Email</td><td style="padding: 6px;"><strong>{user.email}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Role</td><td style="padding: 6px;"><strong>Parent/Guardian</strong></td></tr>
    </table>
    <p>You can now check your children in and out, view attendance records, and manage your profile.</p>
    <div style="text-align: center; margin: 24px 0;">
      <a href="{settings.SITE_URL}/accounts/login/" style="background: #4CAF50; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">Log In Now</a>
    </div>
    <p style="color: #888; font-size: 13px;">If you did not create this account, please contact us immediately.</p>
  </div>
</body>
</html>
    """.strip()

    return send_notification_email(user.email, subject, text_body, html_body)


def send_staff_welcome_email(user, staff_profile):
    """Send welcome email to a newly created staff member."""
    subject = f"Staff Account Created – {settings.SITE_NAME}"
    text_body = f"""
Hi {user.get_full_name()},

A staff account has been created for you at {settings.SITE_NAME}.

Your Account Details:
  Username: {user.username}
  Email: {user.email}
  Position: {staff_profile.position}
  Employee ID: {staff_profile.employee_id or 'N/A'}
  Access Level: {staff_profile.get_access_level_display()}

Log in here: {settings.SITE_URL}/accounts/login/

Please change your password after your first login.

Regards,
The {settings.SITE_NAME} Administration
    """.strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
  <div style="background: #2196F3; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0;">Staff Account Created 👋</h1>
  </div>
  <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>Hi <strong>{user.get_full_name()}</strong>,</p>
    <p>A staff account has been set up for you at <strong>{settings.SITE_NAME}</strong>.</p>
    <table style="background: white; padding: 16px; border-radius: 6px; width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 6px; color: #888;">Username</td><td style="padding: 6px;"><strong>{user.username}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Email</td><td style="padding: 6px;"><strong>{user.email}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Position</td><td style="padding: 6px;"><strong>{staff_profile.position}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Employee ID</td><td style="padding: 6px;"><strong>{staff_profile.employee_id or 'N/A'}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Access Level</td><td style="padding: 6px;"><strong>{staff_profile.get_access_level_display()}</strong></td></tr>
    </table>
    <div style="text-align: center; margin: 24px 0;">
      <a href="{settings.SITE_URL}/accounts/login/" style="background: #2196F3; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">Log In Now</a>
    </div>
    <p style="color: #e53935; font-size: 13px;"><strong>Important:</strong> Please change your password after your first login.</p>
  </div>
</body>
</html>
    """.strip()

    return send_notification_email(user.email, subject, text_body, html_body)


def send_admin_new_parent_notification(admin_user, new_parent):
    """Notify admin when a new parent registers."""
    subject = f"New Parent Registered – {new_parent.get_full_name()}"
    text_body = f"""
Hi {admin_user.get_full_name()},

A new parent has registered on {settings.SITE_NAME}.

Parent Details:
  Name: {new_parent.get_full_name()}
  Username: {new_parent.username}
  Email: {new_parent.email}
  Phone: {new_parent.phone or 'Not provided'}
  Registered At: {new_parent.created_at.strftime('%d %b %Y, %I:%M %p')}

View their profile in the admin panel: {settings.SITE_URL}/custom-admin/accounts/user/{new_parent.pk}/change/

Regards,
{settings.SITE_NAME} System
    """.strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
  <div style="background: #FF9800; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0;">New Parent Registered 🆕</h1>
  </div>
  <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>Hi <strong>{admin_user.get_full_name()}</strong>,</p>
    <p>A new parent has just registered on <strong>{settings.SITE_NAME}</strong>.</p>
    <table style="background: white; padding: 16px; border-radius: 6px; width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 6px; color: #888;">Name</td><td style="padding: 6px;"><strong>{new_parent.get_full_name()}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Username</td><td style="padding: 6px;"><strong>{new_parent.username}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Email</td><td style="padding: 6px;"><strong>{new_parent.email}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Phone</td><td style="padding: 6px;"><strong>{new_parent.phone or 'Not provided'}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Registered At</td><td style="padding: 6px;"><strong>{new_parent.created_at.strftime('%d %b %Y, %I:%M %p')}</strong></td></tr>
    </table>
    <div style="text-align: center; margin: 24px 0;">
      <a href="{settings.SITE_URL}/custom-admin/accounts/user/{new_parent.pk}/change/" style="background: #FF9800; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">View in Admin Panel</a>
    </div>
  </div>
</body>
</html>
    """.strip()

    return send_notification_email(admin_user.email, subject, text_body, html_body)


# ─────────────────────────────────────────────
# CHECK-IN / CHECK-OUT EMAILS
# ─────────────────────────────────────────────

def send_checkin_notification(checkin):
    """Notify parent when their child is checked in."""
    parent = checkin.student.parent
    student = checkin.student
    check_in_time = checkin.check_in_time.astimezone(timezone.get_current_timezone())

    subject = f"✅ {student.get_full_name()} has been checked in"
    text_body = f"""
Hi {parent.get_full_name()},

{student.get_full_name()} has been successfully checked in at {settings.SITE_NAME}.

Check-In Details:
  Student: {student.get_full_name()}
  Room: {checkin.room.name if checkin.room else 'N/A'}
  Check-In Time: {check_in_time.strftime('%I:%M %p, %d %b %Y')}
  Checked In By: {checkin.check_in_by.get_full_name() if checkin.check_in_by else 'N/A'}
  Health Status: {'Healthy ✅' if checkin.is_healthy else 'Health concern noted ⚠️'}
  {f'Health Notes: {checkin.health_notes}' if checkin.health_notes else ''}

View attendance records: {settings.SITE_URL}/attendance/attendance/

Regards,
{settings.SITE_NAME}
    """.strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
  <div style="background: #4CAF50; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0;">✅ Check-In Confirmed</h1>
  </div>
  <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>Hi <strong>{parent.get_full_name()}</strong>,</p>
    <p><strong>{student.get_full_name()}</strong> has been checked in successfully.</p>
    <table style="background: white; padding: 16px; border-radius: 6px; width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 6px; color: #888;">Student</td><td style="padding: 6px;"><strong>{student.get_full_name()}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Room</td><td style="padding: 6px;"><strong>{checkin.room.name if checkin.room else 'N/A'}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Check-In Time</td><td style="padding: 6px;"><strong>{check_in_time.strftime('%I:%M %p, %d %b %Y')}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Checked In By</td><td style="padding: 6px;"><strong>{checkin.check_in_by.get_full_name() if checkin.check_in_by else 'N/A'}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Health Status</td><td style="padding: 6px;"><strong>{'✅ Healthy' if checkin.is_healthy else '⚠️ Health concern noted'}</strong></td></tr>
      {f'<tr><td style="padding: 6px; color: #888;">Health Notes</td><td style="padding: 6px;"><strong>{checkin.health_notes}</strong></td></tr>' if checkin.health_notes else ''}
    </table>
    <div style="text-align: center; margin: 24px 0;">
      <a href="{settings.SITE_URL}/attendance/attendance/" style="background: #4CAF50; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">View Attendance Records</a>
    </div>
  </div>
</body>
</html>
    """.strip()

    # Only send if parent has email notifications enabled
    try:
        if parent.parent_profile.receive_email_notifications:
            return send_notification_email(parent.email, subject, text_body, html_body)
    except Exception:
        pass
    return False


def send_checkout_notification(checkin):
    """Notify parent when their child is checked out."""
    parent = checkin.student.parent
    student = checkin.student
    check_out_time = checkin.check_out_time.astimezone(timezone.get_current_timezone())

    subject = f"👋 {student.get_full_name()} has been checked out"
    text_body = f"""
Hi {parent.get_full_name()},

{student.get_full_name()} has been checked out from {settings.SITE_NAME}.

Check-Out Details:
  Student: {student.get_full_name()}
  Room: {checkin.room.name if checkin.room else 'N/A'}
  Check-Out Time: {check_out_time.strftime('%I:%M %p, %d %b %Y')}
  Time at Daycare: {checkin.duration}
  Checked Out By: {checkin.check_out_by.get_full_name() if checkin.check_out_by else 'N/A'}

View attendance records: {settings.SITE_URL}/attendance/attendance/

Regards,
{settings.SITE_NAME}
    """.strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
  <div style="background: #9C27B0; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0;">👋 Check-Out Confirmed</h1>
  </div>
  <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>Hi <strong>{parent.get_full_name()}</strong>,</p>
    <p><strong>{student.get_full_name()}</strong> has been checked out.</p>
    <table style="background: white; padding: 16px; border-radius: 6px; width: 100%; border-collapse: collapse;">
      <tr><td style="padding: 6px; color: #888;">Student</td><td style="padding: 6px;"><strong>{student.get_full_name()}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Room</td><td style="padding: 6px;"><strong>{checkin.room.name if checkin.room else 'N/A'}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Check-Out Time</td><td style="padding: 6px;"><strong>{check_out_time.strftime('%I:%M %p, %d %b %Y')}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Time at Daycare</td><td style="padding: 6px;"><strong>{checkin.duration}</strong></td></tr>
      <tr><td style="padding: 6px; color: #888;">Checked Out By</td><td style="padding: 6px;"><strong>{checkin.check_out_by.get_full_name() if checkin.check_out_by else 'N/A'}</strong></td></tr>
    </table>
    <div style="text-align: center; margin: 24px 0;">
      <a href="{settings.SITE_URL}/attendance/attendance/" style="background: #9C27B0; color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-weight: bold;">View Attendance Records</a>
    </div>
  </div>
</body>
</html>
    """.strip()

    try:
        if parent.parent_profile.receive_email_notifications:
            return send_notification_email(parent.email, subject, text_body, html_body)
    except Exception:
        pass
    return False


# ─────────────────────────────────────────────
# STAFF TIMECARD EMAILS
# ─────────────────────────────────────────────

def send_staff_clockin_notification(timecard):
    """Notify admin when a staff member clocks in."""
    from accounts.models import User
    admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
    staff = timecard.staff
    clock_in_time = timecard.clock_in_time.astimezone(timezone.get_current_timezone())

    subject = f"🕐 {staff.get_full_name()} has clocked in"
    for admin in admins:
        text_body = f"""
Hi {admin.get_full_name()},

{staff.get_full_name()} has clocked in at {settings.SITE_NAME}.

Timecard Details:
  Staff: {staff.get_full_name()}
  Position: {staff.staff_profile.position if hasattr(staff, 'staff_profile') else 'N/A'}
  Clock-In Time: {clock_in_time.strftime('%I:%M %p, %d %b %Y')}
  Assigned Room: {timecard.assigned_room.name if timecard.assigned_room else 'N/A'}

View timecards: {settings.SITE_URL}/attendance/timecards/

Regards,
{settings.SITE_NAME} System
        """.strip()

        send_notification_email(admin.email, subject, text_body)


def send_staff_clockout_notification(timecard):
    """Notify admin when a staff member clocks out."""
    from accounts.models import User
    admins = User.objects.filter(role=User.Role.ADMIN, is_active=True)
    staff = timecard.staff
    clock_out_time = timecard.clock_out_time.astimezone(timezone.get_current_timezone())

    subject = f"🕔 {staff.get_full_name()} has clocked out"
    for admin in admins:
        text_body = f"""
Hi {admin.get_full_name()},

{staff.get_full_name()} has clocked out at {settings.SITE_NAME}.

Timecard Details:
  Staff: {staff.get_full_name()}
  Clock-Out Time: {clock_out_time.strftime('%I:%M %p, %d %b %Y')}
  Total Hours: {timecard.total_hours}
  Assigned Room: {timecard.assigned_room.name if timecard.assigned_room else 'N/A'}

View timecards: {settings.SITE_URL}/attendance/timecards/

Regards,
{settings.SITE_NAME} System
        """.strip()

        send_notification_email(admin.email, subject, text_body)


# ─────────────────────────────────────────────
# PROFILE UPDATE EMAIL
# ─────────────────────────────────────────────

def send_profile_updated_email(user):
    """Notify user when their profile is updated."""
    subject = f"Your profile was updated – {settings.SITE_NAME}"
    text_body = f"""
Hi {user.get_full_name()},

Your profile on {settings.SITE_NAME} was just updated.

Updated At: {timezone.now().astimezone(timezone.get_current_timezone()).strftime('%I:%M %p, %d %b %Y')}

If you did not make this change, please contact us immediately or reset your password.

Regards,
{settings.SITE_NAME}
    """.strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
  <div style="background: #607D8B; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0;">Profile Updated 🔄</h1>
  </div>
  <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>Hi <strong>{user.get_full_name()}</strong>,</p>
    <p>Your profile on <strong>{settings.SITE_NAME}</strong> was just updated.</p>
    <p><strong>Updated At:</strong> {timezone.now().astimezone(timezone.get_current_timezone()).strftime('%I:%M %p, %d %b %Y')}</p>
    <p style="background: #fff3cd; padding: 12px; border-radius: 6px; color: #856404;">
      ⚠️ If you did not make this change, please contact us immediately or reset your password.
    </p>
  </div>
</body>
</html>
    """.strip()

    return send_notification_email(user.email, subject, text_body, html_body)


def send_checkin_code_updated_email(user):
    """Notify user when their check-in code is changed."""
    subject = f"Your check-in code was updated – {settings.SITE_NAME}"
    text_body = f"""
Hi {user.get_full_name()},

Your check-in code on {settings.SITE_NAME} has been updated.

Updated At: {timezone.now().astimezone(timezone.get_current_timezone()).strftime('%I:%M %p, %d %b %Y')}

Keep your check-in code private. Do not share it with anyone other than authorized guardians.

If you did not request this change, please contact us immediately.

Regards,
{settings.SITE_NAME}
    """.strip()

    html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; color: #333;">
  <div style="background: #F44336; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
    <h1 style="color: white; margin: 0;">Check-In Code Updated 🔑</h1>
  </div>
  <div style="background: #f9f9f9; padding: 24px; border-radius: 0 0 8px 8px;">
    <p>Hi <strong>{user.get_full_name()}</strong>,</p>
    <p>Your check-in code on <strong>{settings.SITE_NAME}</strong> has been changed.</p>
    <p><strong>Updated At:</strong> {timezone.now().astimezone(timezone.get_current_timezone()).strftime('%I:%M %p, %d %b %Y')}</p>
    <p style="background: #ffebee; padding: 12px; border-radius: 6px; color: #c62828;">
      🔒 Keep your check-in code private. If you did not request this change, please contact us immediately.
    </p>
  </div>
</body>
</html>
    """.strip()

    return send_notification_email(user.email, subject, text_body, html_body)