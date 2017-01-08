from django import forms

from network.base.models import Station


class StationForm(forms.ModelForm):
    class Meta:
        model = Station
        fields = ['name', 'image', 'alt', 'rig', 'uuid',
                  'lat', 'lng', 'qthlocator',
                  'horizon', 'antenna', 'active']
        image = forms.ImageField(required=False)


class SatelliteFilterForm(forms.Form):
    norad = forms.IntegerField()
    start_date = forms.CharField(required=False)
    end_date = forms.CharField(required=False)
    ground_station = forms.IntegerField(required=False)
