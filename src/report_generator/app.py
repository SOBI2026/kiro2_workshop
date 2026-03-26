import json
import os
import sys
import boto3
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.logger import get_logger
from common.error_handler import handle_lambda_error
from common.rds_helper import RDSHelper

logger = get_logger(__name__)
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

def generate_daily_report(user_id, user_name, activity_data):
    """Generate daily activity summary"""
    total_activities = len(activity_data)
    
    # Calculate hourly distribution
    hourly_dist = [0] * 24
    for activity in activity_data:
        hour = activity['timestamp'].hour
        hourly_dist[hour] += 1
    
    # Count alerts
    alert_count = sum(1 for a in activity_data if a['activity_type'] == 'alert')
    
    report = {
        'userId': user_id,
        'userName': user_name,
        'reportType': 'daily',
        'date': datetime.utcnow().strftime('%Y-%m-%d'),
        'totalActivities': total_activities,
        'hourlyDistribution': hourly_dist,
        'alertCount': alert_count
    }
    
    return report

def generate_monthly_pdf(user_id, user_name, activity_data, output_path):
    """Generate monthly PDF report"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, f"Monthly Activity Report")
    
    # User info
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"User: {user_name}")
    c.drawString(50, height - 100, f"User ID: {user_id}")
    c.drawString(50, height - 120, f"Report Date: {datetime.utcnow().strftime('%Y-%m')}")
    
    # Statistics
    total_activities = len(activity_data)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 160, "Activity Summary")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 180, f"Total Activities: {total_activities}")
    
    # Calculate daily average
    if activity_data:
        days_in_period = 30
        daily_avg = total_activities / days_in_period
        c.drawString(50, height - 200, f"Daily Average: {daily_avg:.1f}")
    
    # Alert count
    alert_count = sum(1 for a in activity_data if a.get('activity_type') == 'alert')
    c.drawString(50, height - 220, f"Alerts: {alert_count}")
    
    # Footer
    c.setFont("Helvetica", 10)
    c.drawString(50, 30, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    c.save()
    
    # Write to file
    buffer.seek(0)
    with open(output_path, 'wb') as f:
        f.write(buffer.read())
    
    logger.info(f"Generated PDF report: {output_path}")

@handle_lambda_error
def lambda_handler(event, context):
    """
    Generate daily and monthly activity reports
    Triggered by EventBridge schedule
    """
    logger.info("Starting report generation")
    
    # Determine report type from event
    report_type = event.get('reportType', 'daily')
    
    rds = RDSHelper()
    
    # Get all active users
    with rds.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name FROM users WHERE status = 'active'")
        users = cursor.fetchall()
    
    logger.info(f"Generating {report_type} reports for {len(users)} users")
    
    reports_generated = 0
    
    for user_id, user_name in users:
        try:
            # Determine date range
            if report_type == 'daily':
                start_date = datetime.utcnow() - timedelta(days=1)
                end_date = datetime.utcnow()
            else:  # monthly
                start_date = datetime.utcnow() - timedelta(days=30)
                end_date = datetime.utcnow()
            
            # Get activity data
            activity_data = rds.get_activity_history(str(user_id), start_date, end_date)
            
            if report_type == 'daily':
                # Generate daily summary
                report = generate_daily_report(str(user_id), user_name, activity_data)
                
                # Publish to SNS
                sns_client.publish(
                    TopicArn=os.environ['SNS_REPORT_TOPIC_ARN'],
                    Subject=f'일일 활동 리포트 - {user_name}',
                    Message=json.dumps(report, ensure_ascii=False, indent=2)
                )
                
                logger.info(f"Published daily report for user {user_id}")
                
            else:  # monthly
                # Generate PDF
                now = datetime.utcnow()
                year = now.strftime('%Y')
                month = now.strftime('%m')
                
                pdf_filename = f'/tmp/report_{user_id}.pdf'
                generate_monthly_pdf(str(user_id), user_name, activity_data, pdf_filename)
                
                # Upload to S3
                s3_key = f'reports/{year}/{month}/{user_id}/report.pdf'
                bucket_name = os.environ['REPORTS_BUCKET_NAME']
                
                s3_client.upload_file(
                    pdf_filename,
                    bucket_name,
                    s3_key,
                    ExtraArgs={'ServerSideEncryption': 'aws:kms'}
                )
                
                # Generate presigned URL
                download_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': s3_key},
                    ExpiresIn=604800  # 7 days
                )
                
                # Publish to SNS with download link
                sns_client.publish(
                    TopicArn=os.environ['SNS_REPORT_TOPIC_ARN'],
                    Subject=f'월간 활동 리포트 - {user_name}',
                    Message=f"""
{user_name}님의 월간 활동 리포트가 생성되었습니다.

기간: {year}년 {month}월
총 활동 횟수: {len(activity_data)}

다운로드 링크 (7일간 유효):
{download_url}
                    """.strip()
                )
                
                logger.info(f"Published monthly report for user {user_id} to S3: {s3_key}")
            
            reports_generated += 1
            
        except Exception as e:
            logger.error(f"Error generating report for user {user_id}: {str(e)}")
    
    logger.info(f"Report generation complete. Generated {reports_generated} reports")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Report generation complete',
            'reportType': report_type,
            'reportsGenerated': reports_generated
        })
    }
