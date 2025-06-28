import random
from django.core.management.base import BaseCommand
from faker import Faker
from django.core.files import File
from pathlib import Path
from django.contrib.auth.hashers import make_password
from django.conf import settings

from apps.dashboard.models import User, Document  # Adjust if your import path differs

class Command(BaseCommand):
    help = 'Generate fake users and documents with titles, descriptions, and files'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Image and PDF directories
        profile_image_dir = Path(settings.MEDIA_ROOT) / 'fake_profiles'
        pdf_dir = Path(settings.MEDIA_ROOT) / 'fake_pdfs'

        # Collect available media
        profile_images = list(profile_image_dir.glob('*.jpg')) + list(profile_image_dir.glob('*.png'))
        pdf_files = list(pdf_dir.glob('*.pdf'))

        if not profile_images:
            self.stdout.write(self.style.WARNING("⚠️ No profile images found in media/fake_profiles/"))
        if not pdf_files:
            self.stdout.write(self.style.WARNING("⚠️ No PDFs found in media/fake_pdfs/"))

        for _ in range(15):  # Number of users to generate
            name = fake.user_name()
            email = fake.email()
            mobile = fake.msisdn()[:10]
            password = make_password("test1234")
            bio = fake.sentence(nb_words=12)

            # Create user
            user = User.objects.create(
                name=name,
                email=email,
                mobile=f"+91{mobile}",
                password=password,
                is_active=True,
                bio=bio,
            )

            # Assign profile image
            if profile_images:
                selected_image = random.choice(profile_images)
                with open(selected_image, 'rb') as img_file:
                    user.profile_image.save(selected_image.name, File(img_file), save=True)

            # Generate 2–4 documents per user
            for _ in range(random.randint(2, 4)):
                title = fake.catch_phrase()
                description = fake.paragraph(nb_sentences=2)

                doc = Document.objects.create(
                    user=user,
                    title=title,
                    description=description
                )

                # Assign PDF file
                if pdf_files:
                    selected_pdf = random.choice(pdf_files)
                    with open(selected_pdf, 'rb') as pdf_file:
                        doc.file.save(selected_pdf.name, File(pdf_file), save=True)

        self.stdout.write(self.style.SUCCESS("✅ Successfully generated fake users and documents."))
