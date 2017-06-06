import os
from datetime import datetime, timedelta
from shortuuidfield import ShortUUIDField

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.timezone import now
from django.conf import settings
from django.utils.html import format_html

from network.users.models import User
from network.base.helpers import get_apikey


RIG_TYPES = ['Radio', 'SDR']
ANTENNA_BANDS = ['HF', 'VHF', 'UHF', 'L', 'S', 'C', 'X', 'KU']
ANTENNA_TYPES = (
    ('dipole', 'Dipole'),
    ('yagi', 'Yagi'),
    ('helical', 'Helical'),
    ('parabolic', 'Parabolic'),
    ('vertical', 'Verical'),
    ('turnstile', 'Turnstile'),
    ('quadrafilar', 'Quadrafilar'),
    ('eggbeater', 'Eggbeater'),
    ('lindenblad', 'Lindenblad'),
)
OBSERVATION_STATUSES = (
    ('unknown', 'Unknown'),
    ('verified', 'Verified'),
    ('data_not_verified', 'Has Data, Not Verified'),
    ('no_data', 'No Data'),
)


class Rig(models.Model):
    name = models.CharField(choices=zip(RIG_TYPES, RIG_TYPES), max_length=10)
    rictld_number = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        return '{0}: {1}'.format(self.name, self.rictld_number)


class Mode(models.Model):
    name = models.CharField(max_length=10, unique=True)

    def __unicode__(self):
        return self.name


class Antenna(models.Model):
    """Model for antennas tracked with SatNOGS."""
    frequency = models.PositiveIntegerField()
    frequency_max = models.PositiveIntegerField()
    band = models.CharField(choices=zip(ANTENNA_BANDS, ANTENNA_BANDS),
                            max_length=5)
    antenna_type = models.CharField(choices=ANTENNA_TYPES, max_length=15)

    def __unicode__(self):
        return '{0} - {1} - {2} - {3}'.format(self.band, self.antenna_type,
                                              self.frequency,
                                              self.frequency_max)


class Station(models.Model):
    """Model for SatNOGS ground stations."""
    owner = models.ForeignKey(User)
    name = models.CharField(max_length=45)
    image = models.ImageField(upload_to='ground_stations', blank=True)
    alt = models.PositiveIntegerField(help_text='In meters above ground')
    lat = models.FloatField(validators=[MaxValueValidator(90),
                                        MinValueValidator(-90)])
    lng = models.FloatField(validators=[MaxValueValidator(180),
                                        MinValueValidator(-180)])
    qthlocator = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    antenna = models.ManyToManyField(Antenna, blank=True,
                                     help_text=('If you want to add a new Antenna contact '
                                                '<a href="https://community.satnogs.org/" '
                                                'target="_blank">SatNOGS Team</a>'))
    featured_date = models.DateField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    horizon = models.PositiveIntegerField(help_text='In degrees above 0', default=10)
    uuid = models.CharField(db_index=True, max_length=100, blank=True)
    rig = models.ForeignKey(Rig, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-active', '-last_seen']

    def get_image(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        else:
            return settings.STATION_DEFAULT_IMAGE

    @property
    def online(self):
        try:
            heartbeat = self.last_seen + timedelta(minutes=int(settings.STATION_HEARTBEAT_TIME))
            return self.active and heartbeat > now()
        except:
            return False

    def state(self):
        if self.online:
            return format_html('<span style="color:green">Online</span>')
        else:
            return format_html('<span style="color:red">Offline</span>')

    @property
    def success_rate(self):
        observations = self.data_set.all().count()
        success = self.data_set.exclude(payload='').count()
        if observations:
            return int(100 * (float(success) / float(observations)))
        else:
            return False

    @property
    def apikey(self):
        return get_apikey(user=self.owner)

    def __unicode__(self):
        return "%d - %s" % (self.pk, self.name)


class Satellite(models.Model):
    """Model for SatNOGS satellites."""
    norad_cat_id = models.PositiveIntegerField()
    name = models.CharField(max_length=45)
    names = models.TextField(blank=True)
    image = models.CharField(max_length=100, blank=True, null=True)
    manual_tle = models.BooleanField(default=False)

    class Meta:
        ordering = ['norad_cat_id']

    def get_image(self):
        if self.image:
            return self.image
        else:
            return settings.SATELLITE_DEFAULT_IMAGE

    @property
    def latest_tle(self):
        try:
            latest_tle = Tle.objects.filter(satellite=self).latest('updated')
            return latest_tle
        except Tle.DoesNotExist:
            return False

    @property
    def tle_no(self):
        try:
            line = self.latest_tle.tle1
            return line[65:68]
        except:
            return False

    @property
    def tle_epoch(self):
        try:
            line = self.latest_tle.tle1
            yd, s = line[18:32].split('.')
            epoch = (datetime.strptime(yd, "%y%j") +
                     timedelta(seconds=float("." + s) * 24 * 60 * 60))
            return epoch
        except:
            return False

    @property
    def success_rate(self):
        try:
            data = Data.objects.filter(observation__satellite=self)
            data_verified = float(data.filter(vetted_status='verified').count())
            data_all = float(data.count())
            return int(100 * (data_verified / data_all))
        except:
            return 0

    @property
    def data_count(self):
        return Data.objects.filter(observation__satellite=self).count()

    @property
    def verified_count(self):
        data = Data.objects.filter(observation__satellite=self)
        return data.filter(vetted_status='verified').count()

    @property
    def empty_count(self):
        data = Data.objects.filter(observation__satellite=self)
        return data.filter(vetted_status='no_data').count()

    @property
    def unknown_count(self):
        data = Data.objects.filter(observation__satellite=self)
        return data.filter(vetted_status='unknown').count()

    @property
    def empty_rate(self):
        try:
            data = Data.objects.filter(observation__satellite=self)
            data_empty = float(data.filter(vetted_status='no_data').count())
            data_all = float(data.count())
            return int(100 * (data_empty / data_all))
        except:
            return 0

    @property
    def unknown_rate(self):
        try:
            data = Data.objects.filter(observation__satellite=self)
            data_unknown = float(data.filter(vetted_status='unknown').count())
            data_all = float(data.count())
            return int(100 * (data_unknown / data_all))
        except:
            return 0

    def __unicode__(self):
        return self.name


class Tle(models.Model):
    tle0 = models.CharField(max_length=100, blank=True)
    tle1 = models.CharField(max_length=200, blank=True)
    tle2 = models.CharField(max_length=200, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)
    satellite = models.ForeignKey(Satellite, related_name='tles', null=True)

    class Meta:
        ordering = ['tle0']

    def __unicode__(self):
        return self.tle0


class Transmitter(models.Model):
    """Model for antennas transponders."""
    uuid = ShortUUIDField(db_index=True)
    description = models.TextField()
    alive = models.BooleanField(default=True)
    uplink_low = models.PositiveIntegerField(blank=True, null=True)
    uplink_high = models.PositiveIntegerField(blank=True, null=True)
    downlink_low = models.PositiveIntegerField(blank=True, null=True)
    downlink_high = models.PositiveIntegerField(blank=True, null=True)
    mode = models.ForeignKey(Mode, related_name='transmitters', blank=True,
                             null=True, on_delete=models.SET_NULL)
    invert = models.BooleanField(default=False)
    baud = models.FloatField(validators=[MinValueValidator(0)], null=True, blank=True)
    satellite = models.ForeignKey(Satellite, related_name='transmitters', null=True)

    def __unicode__(self):
        return self.description


class Observation(models.Model):
    """Model for SatNOGS observations."""
    satellite = models.ForeignKey(Satellite)
    transmitter = models.ForeignKey(Transmitter, null=True, related_name='observations')
    tle = models.ForeignKey(Tle, null=True)
    author = models.ForeignKey(User)
    start = models.DateTimeField()
    end = models.DateTimeField()

    class Meta:
        ordering = ['-start', '-end']

    @property
    def is_past(self):
        return self.end < now()

    @property
    def is_future(self):
        return self.end > now()

    @property
    def is_deletable_before_start(self):
        deletion = self.start - timedelta(minutes=int(settings.OBSERVATION_MAX_DELETION_RANGE))
        return deletion > now()

    @property
    def is_deletable_after_end(self):
        deletion = self.end + timedelta(minutes=int(settings.OBSERVATION_MIN_DELETION_RANGE))
        return deletion < now()

    # observation has at least 1 payload submitted, no verification taken into account
    @property
    def has_submitted_data(self):
        return self.data_set.exclude(payload='').count()

    # observaton has at least 1 payload that has been verified good
    @property
    def has_verified_data(self):
        return self.data_set.filter(vetted_status='verified').count()

    # observation is vetted to be all bad data
    @property
    def has_no_data(self):
        return self.data_set.filter(
            vetted_status='no_data').count() == self.data_set.count()

    # observation has at least 1 payload left unvetted
    @property
    def has_unvetted_data(self):
        return self.data_set.filter(vetted_status='unknown').count()

    def __unicode__(self):
        return '{0}'.format(self.id)


class Data(models.Model):
    """Model for observation data."""
    start = models.DateTimeField()
    end = models.DateTimeField()
    observation = models.ForeignKey(Observation)
    ground_station = models.ForeignKey(Station)
    payload = models.FileField(upload_to='data_payloads', blank=True, null=True)
    waterfall = models.ImageField(upload_to='data_waterfalls', blank=True, null=True)
    vetted_datetime = models.DateTimeField(null=True, blank=True)
    vetted_user = models.ForeignKey(User, related_name="vetted_user_set", null=True, blank=True)
    vetted_status = models.CharField(choices=OBSERVATION_STATUSES,
                                     max_length=20, default='unknown')
    rise_azimuth = models.FloatField(blank=True, null=True)
    max_altitude = models.FloatField(blank=True, null=True)
    set_azimuth = models.FloatField(blank=True, null=True)

    @property
    def is_past(self):
        return self.end < now()

    # this payload has been vetted good/bad by someone
    @property
    def is_vetted(self):
        return not self.vetted_status == 'unknown'

    # this payload has been vetted as good by someone
    @property
    def is_verified(self):
        return self.vetted_status == 'verified'

    # this payload has been vetted as bad by someone
    @property
    def is_no_data(self):
        return self.vetted_status == 'no_data'

    @property
    def payload_exists(self):
        """ Run some checks on the payload for existence of data """
        if self.payload is None:
            return False
        if not os.path.isfile(os.path.join(settings.MEDIA_ROOT, self.payload.name)):
            return False
        if self.payload.size == 0:
            return False
        return True

    class Meta:
        ordering = ['-start', '-end']


class DemodData(models.Model):
    data = models.ForeignKey(Data, related_name='demoddata')
    payload_demod = models.FileField(upload_to='data_payloads', blank=True, null=True)

    def display_payload(self):
        with open(self.payload_demod.path) as fp:
            return fp.read()
