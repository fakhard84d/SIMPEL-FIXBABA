from django.core.management.base import BaseCommand
from django.utils import timezone
import openpyxl
from services.models import Customer


class Command(BaseCommand):
    help = 'وارد کردن داده‌ها از فایل اکسل'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='مسیر فایل اکسل')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        try:
            workbook = openpyxl.load_workbook(file_path)
            sheet = workbook.active
            
            customers_created = 0
            customers_updated = 0
            
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row[0]:
                    continue
                
                try:
                    row_number = row[0]
                    bill_number = str(row[1]) if row[1] else None
                    is_warranty = bool(row[2]) if row[2] is not None else False
                    operation_type = row[3] or ''
                    customer_name = row[4] or ''
                    product_type = row[5] or ''
                    acceptance_date = row[6] or ''
                    registration_code = str(row[7]) if row[7] else ''
                    issuer_name = row[8] or ''
                    product_model = row[9] or ''
                    serial_number = row[10] or ''
                    completion_date = row[11] or None
                    address = row[12] or ''
                    has_warranty_card = bool(row[13]) if row[13] is not None else False
                    warranty_card_number = str(row[14]) if row[14] else None
                    phone_number = str(row[15]) if row[15] else ''
                    service_status = row[16] or ''
                    
                    if not bill_number:
                        self.stdout.write(self.style.WARNING(f'ردیف {row_idx}: شماره قبض نامعتبر است'))
                        continue
                    
                    customer, created = Customer.objects.update_or_create(
                        bill_number=bill_number,
                        defaults={
                            'row_number': row_number,
                            'is_warranty': is_warranty,
                            'operation_type': operation_type,
                            'customer_name': customer_name,
                            'product_type': product_type,
                            'acceptance_date': acceptance_date,
                            'registration_code': registration_code,
                            'issuer_name': issuer_name,
                            'product_model': product_model,
                            'serial_number': serial_number,
                            'completion_date': completion_date,
                            'address': address,
                            'has_warranty_card': has_warranty_card,
                            'warranty_card_number': warranty_card_number,
                            'phone_number': phone_number,
                            'service_status': service_status,
                        }
                    )
                    
                    if created:
                        customers_created += 1
                        self.stdout.write(self.style.SUCCESS(f'مشتری جدید: {customer_name} - {bill_number}'))
                        self.stdout.write(self.style.INFO(f'  لینک: /service/{customer.access_token}/'))
                    else:
                        customers_updated += 1
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'خطا در ردیف {row_idx}: {str(e)}'))
            
            self.stdout.write(self.style.SUCCESS(f'\nجمع‌بندی: {customers_created} جدید، {customers_updated} به‌روزرسانی'))
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'فایل یافت نشد: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'خطا: {str(e)}'))
