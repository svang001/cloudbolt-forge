from django import forms

from common.forms import C2Form
from common.methods import generate_string_from_template_for_server
from utilities.logger import ThreadLogger
from utilities.forms import ConnectionInfoForm

logger = ThreadLogger(__name__)


class TintriEndpointForm(ConnectionInfoForm):
    protocol = forms.ChoiceField(
        choices=[('http', 'HTTP'), ('https', 'HTTPS')], label='Protocol')

    def __init__(self, *args, **kwargs):
        super(TintriEndpointForm, self).__init__(*args, **kwargs)

        self.fields["name"].widget = forms.HiddenInput()
        self.fields["name"].initial = "Tintri Appliance Endpoint"
        if not self.initial_instance:
            self.fields["port"].initial = 443
            self.fields["protocol"].initial = "https"

        # ConnectionInfo has support for ssh key which we don't need for Tintri
        del self.fields['ssh_key']
        del self.fields['use_auth_headers']
        del self.fields['headers']

        # mark all fields as required
        for field in list(self.fields.values()):
            field.required = True

        #except the labels field
        self.fields["labels"].required = False

    def clean(self):
        try:
            from xui.tintri.tintri_api import Tintri
            tintri = Tintri()
            tintri.verify_connection(
                self.cleaned_data.get('protocol'),
                self.cleaned_data.get('ip'),
                self.cleaned_data.get('port'),
                self.cleaned_data.get('username'),
                self.cleaned_data.get('password'),
            )
        except:
            raise forms.ValidationError(
                "Unable to connect to Tintri Appliance's Endpoint using the parameters provided "
            )

        return self.cleaned_data

    def save(self, *args, **kwargs):
        endpoint = super(TintriEndpointForm, self).save(*args, **kwargs)
        return endpoint


class TintriSnapshotForm(C2Form):
    duration = forms.ChoiceField(
        choices=[
            ('60', 'One Hour'),
            ('180', "3 Hours"),
            ('1440', "One Day"),
            ('10080', 'One Week'),
            ('-1', 'Never Expires')
        ], label='Duration (in minutes)')

    def __init__(self, *args, **kwargs):
        self.server = kwargs.pop("server")
        super().__init__(*args, **kwargs)

    def save(self):
        return {'snapshot_duration': int(self.cleaned_data['duration'])}

class TintriCloneSnapshotForm(C2Form):
    new_vm_name = forms.CharField(label="New VM Name")

    def __init__(self, *args, **kwargs):
        self.server = kwargs.pop("server")
        super().__init__(*args, **kwargs)

        name_template = "{{ server.hostname }}-tintriclone-00X"
        new_name = generate_string_from_template_for_server(
            name_template, self.server
        )
        self.fields['new_vm_name'].initial = new_name

    def save(self):
        return {'new_vm_name': self.cleaned_data['new_vm_name']}
