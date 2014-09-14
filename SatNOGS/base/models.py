from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.timezone import now

from users.models import User


ANTENNA_BANDS = ['HF', 'VHF', 'UHF', 'L', 'S', 'C', 'X', 'KU']
ANTENNA_TYPES = (
    ('dipole', 'Dipole'),
    ('yagi', 'Yagi'),
    ('helical', 'Helical'),
    ('parabolic', 'Parabolic'),
)
MODE_CHOICES = ['FM', 'AFSK', 'APRS', 'SSTV', 'CW', 'FMN']


class Antenna(models.Model):
    """Model for antennas tracked with SatNOGS."""
    frequency = models.FloatField(validators=[MinValueValidator(0)])
    band = models.CharField(choices=zip(ANTENNA_BANDS, ANTENNA_BANDS),
                            max_length=5)
    antenna_type = models.CharField(choices=ANTENNA_TYPES, max_length=15)


class Station(models.Model):
    """Model for SatNOGS ground stations."""
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=45)
    image = models.ImageField(upload_to='ground_stations')
    alt = models.PositiveIntegerField()
    lat = models.FloatField(validators=[MaxValueValidator(90),
                                        MinValueValidator(-90)])
    lng = models.FloatField(validators=[MaxValueValidator(180),
                                        MinValueValidator(-180)])
    antenna = models.ManyToManyField(Antenna)
    featured = models.BooleanField(default=False)


class Satellite(models.Model):
    """Model for SatNOGS satellites."""
    norad_cat_id = models.PositiveIntegerField()
    name = models.CharField(max_length=45)


class Transponder(models.Model):
    """Model for antennas transponders."""
    description = models.TextField()
    alive = models.BooleanField()
    uplink_low = models.PositiveIntegerField()
    uplink_high = models.PositiveIntegerField()
    downlink_low = models.PositiveIntegerField()
    downlink_high = models.PositiveIntegerField()
    mode = models.CharField(choices=zip(MODE_CHOICES, MODE_CHOICES),
                            max_length=10)
    invert = models.BooleanField()
    baud = models.FloatField(validators=[MinValueValidator(0)])
    satellite = models.ForeignKey(Satellite, related_name='transponder',
                                  null=True)


class Observation(models.Model):
    """Model for SatNOGS observations."""
    satellite = models.ForeignKey(Satellite)
    author = models.ForeignKey(User)
    start = models.DateTimeField()
    end = models.DateTimeField()

    @property
    def is_past(self):
        return self.end < now()

    @property
    def is_future(self):
        return self.end > now()


class Data(models.Model):
    """Model for observation data."""
    url = models.URLField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    observation = models.ForeignKey(Observation)
    ground_station = models.ForeignKey(Station)
