# Generated by Django 4.0 on 2022-01-02 15:31

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('importance', models.SmallIntegerField(default=0)),
                ('publishDate', models.DateTimeField(default=datetime.datetime.now)),
                ('image', models.ImageField(upload_to='images/articleMain')),
                ('article', models.TextField()),
                ('visits', models.PositiveIntegerField(default=0)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts', to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('writer', models.CharField(default='ناشناس', max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('date', models.DateTimeField(default=datetime.datetime.now)),
                ('text', models.TextField(max_length=2000)),
                ('is_accepted', models.BooleanField(default=False)),
                ('reply', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repliedOn', to='News.comment')),
            ],
        ),
    ]
