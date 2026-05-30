using LiveWell.Networking;

namespace LiveWell.Pages;

public partial class WelcomingPage : ContentPage
{
	public WelcomingPage()
	{
		InitializeComponent();
        NavigatedTo += (e, args) =>
        {
            if (Account.Current.profile == null || string.IsNullOrEmpty(Account.Current.profile.user_id))
                return;
            Navigation.PopModalAsync();
        };
    }

    private void Button_Clicked(object sender, EventArgs e)
    {
        try
        {
            Navigation.PushModalAsync(new EditProfilePage());
        }
        catch (Exception ex)
        {
            DisplayAlert("Error", ex.Message, "OK");
        }
    }
}