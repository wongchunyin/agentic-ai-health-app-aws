using LiveWell.Networking;
using LiveWell.Pages;
using LiveWell.Views;
using System.Diagnostics;

namespace LiveWell
{
    public partial class MainPage : ContentPage
    {
        public MainPage()
        {
            InitializeComponent();
            NavigatedTo += async (e, args) => await UpdatePage();
        }

        public async Task UpdatePage()
        {
            LoadingIndicator.IsVisible = true;
            try
            {
                if (Account.Current == null)
                {
                    await Account.Initialize();
                }

                if (!string.IsNullOrEmpty(Account.Current?.profile?.preferred_name))
                    WelcomeLabel.Text = $"Welcome, {Account.Current?.profile?.preferred_name}";
                else if (!string.IsNullOrEmpty(Account.Current?.profile?.first_name))
                    WelcomeLabel.Text = $"Welcome, {Account.Current?.profile?.first_name}";
                else if (!string.IsNullOrEmpty(Account.Current?.profile?.family_name))
                    WelcomeLabel.Text = $"Welcome, {Account.Current?.profile?.family_name}";
                else
                    WelcomeLabel.Text = "Welcome!";

                string? activity_score = Account.Current?.profile?.activity_score.ToString();
                LblActivityScore.Text = string.IsNullOrWhiteSpace(activity_score) ? "N/A" : activity_score;
                LblTemperature.Text = "20°C";
                LblMinMaxTemp.Text = "12°C / 22°C";
                LblDescription.Text = "Partly Cloudy";
                plansLayout.Clear();
                Account.Current!.schedule_tasks = await NetworkingAPI.GetScheduleTasks();

                var plans = await NetworkingAPI.GetPlan();
                if (plans is not null)
                {
                    foreach (var plan in plans)
                    {
                        plansLayout.Add(new PlanView(plan));
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.Print(ex.Message);
                await DisplayAlert("Error", $"Failed to load profile information.\nError: {ex.Message}", "OK");
            }
            LoadingIndicator.IsVisible = false;
            await UpdateWeatherInfo();
        }

        private async Task<string> GetCurrentLocality(Location location)
        {
            var placemarks = await Geocoding.GetPlacemarksAsync(location);
            if (placemarks == null || !placemarks.Any())
            {
                throw new Exception("Unable to get placemarks from current location.");
            }
            var placemark = placemarks?.FirstOrDefault();
            if (placemark == null)
            {
                throw new Exception("Unable to get placemark from current location.");
            }
            return placemark.Locality;
        }

        private async Task UpdateWeatherInfo()
        {
            Location? location = await Geolocation.GetLocationAsync();
            if (location == null)
            {
                throw new Exception("Unable to get current location.");
            }
            string locality = await GetCurrentLocality(location);

            LblLocation.Text = locality;
        }

        private async void ImageButton_Clicked(object sender, EventArgs e)
        {
            try
            {
                string action = await DisplayActionSheet("Profile Options", "Cancel", null, "Edit Profile", "Log Out");
                if (action == "Log Out")
                {
                    bool confirm = await DisplayAlert("Log Out", "Are you sure you want to log out?", "Log Out", "Cancel");
                    if (!confirm)
                    {
                        return;
                    }
                    LoadingIndicator.IsVisible = true;
                    await Account.Current!.Logout();
                }
                else if (action == "Edit Profile")
                {
                    await Navigation.PushAsync(new EditProfilePage());
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", ex.Message, "OK");
            }
        }

        private async void BtnAddPlan_Clicked(object sender, EventArgs e)
        {
            try
            {
                string plan_type = await DisplayActionSheet("Select Plan Creation Method", "Cancel", null, "Create AI-Generated Plan", "Create Custom Plan");

                if (plan_type == "Create AI-Generated Plan")
                {
                    string desc = "Describe the type of exercise you would like for this plan:";
                    string action_type = await DisplayPromptAsync("AI Plan", desc, "OK", "Cancel", "E.g. physical, mental");
                    await Navigation.PushAsync(new EditPlanPage(action_type));
                }
                else if (plan_type == "Create Custom Plan")
                {
                    await Navigation.PushAsync(new EditPlanPage());
                }
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", ex.Message, "OK");
            }
        }
    }
}
