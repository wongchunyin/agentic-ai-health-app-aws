using LiveWell.Models;
using LiveWell.Networking;

namespace LiveWell.Pages;

public partial class EditProfilePage : ContentPage
{
    bool isNewProfile = false;

    public EditProfilePage()
	{
		InitializeComponent();
        isNewProfile = Account.Current?.profile == null;
        if (isNewProfile)
        {
            Title = "Create Profile";
        }
        else
        {
            Title = "Edit Profile";
            EntryEmail.Text = Account.Current!.profile!.email;
            EntryFirstName.Text = Account.Current!.profile!.first_name;
            EntryLastName.Text = Account.Current!.profile!.family_name;
            EntryPreferredName.Text = Account.Current!.profile!.preferred_name;
            EntryDOB.Text = Account.Current!.profile!.dob;
            PickerGender.SelectedItem = Account.Current!.profile!.gender;
            if (Account.Current!.profile!.address != null)
            {
                EntryStreet.Text = Account.Current!.profile!.address!.street;
                EntryCity.Text = Account.Current!.profile!.address!.city;
                EntryCountry.Text = Account.Current!.profile!.address!.country;
            }
        }
    }

	private async void BtnSave_Clicked(object sender, EventArgs e)
	{
        LoadingIndicator.IsVisible = true;
        try
        {
            if (string.IsNullOrEmpty(EntryEmail.Text) ||
                string.IsNullOrEmpty(EntryFirstName.Text) ||
                string.IsNullOrEmpty(EntryLastName.Text))
            {
                string message = "These fields must not be empty: ";
                if (string.IsNullOrEmpty(EntryEmail.Text))
                    message += "Email, ";
                if (string.IsNullOrEmpty(EntryFirstName.Text))
                    message += "First name, ";
                if (string.IsNullOrEmpty(EntryLastName.Text))
                    message += "Last name, ";
                message = message.Substring(0, message.LastIndexOf(","));
                throw new ArgumentNullException(message);
            }

            var profile = new Profile
            {
                user_id = isNewProfile ? null : Account.Current!.profile!.user_id,
                email = EntryEmail.Text,
                first_name = EntryFirstName.Text,
                family_name = EntryLastName.Text,
            };
            if (!string.IsNullOrEmpty(EntryPreferredName.Text))
                profile.preferred_name = EntryPreferredName.Text;
            if (!string.IsNullOrEmpty(EntryDOB.Text))
                profile.dob = EntryDOB.Text;
            if (!string.IsNullOrEmpty(PickerGender.SelectedItem as string))
                profile.gender = PickerGender.SelectedItem as string;
            if (!string.IsNullOrEmpty(EntryStreet.Text) ||
                !string.IsNullOrEmpty(EntryCity.Text) ||
                !string.IsNullOrEmpty(EntryCountry.Text))
            {
                profile.address = new Profile.Address
                {
                    street = EntryStreet.Text,
                    city = EntryCity.Text,
                    country = EntryCountry.Text
                };
            }

            if (isNewProfile)
            {
                profile.activity_score = 0;
                Account.Current!.profile = await NetworkingAPI.SaveProfile(profile);
                await DisplayAlert("Profile", "Profile created successfully.", "OK");
                await Navigation.PopModalAsync();
            }
            else
            {
                profile.activity_score = Account.Current!.profile!.activity_score ?? 0;
                var updatedProfile = await NetworkingAPI.UpdateProfile(profile);
                if (updatedProfile == null)
                {
                    throw new Exception("Failed to update profile.");
                }
                Account.Current!.profile = updatedProfile;
                await DisplayAlert("Profile", "Profile updated successfully.", "OK");
            }
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", $"Failed to save profile.\nError: {ex.Message}", "OK");
        }
        LoadingIndicator.IsVisible = false;
    }
}