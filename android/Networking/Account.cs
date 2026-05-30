using LiveWell.Models;
using System.Diagnostics;
using System.IdentityModel.Tokens.Jwt;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace LiveWell.Networking
{
    public class Account
    {
        public Profile? profile;
        public List<Plan> plans = new List<Plan>();
        public Token? token;
        public List<ScheduleTask>? schedule_tasks;

        public Account(Token token)
        {
            this.token = token;
            _ = get_weather_forecast();
        }

        public async Task Logout()
        {
            string loginUrl = @"https://livewell.auth.us-east-1.amazoncognito.com/logout?client_id=6s89mphvvhjr5lt7es4v0ap55q&logout_uri=yourapp%3A%2F%2Flogout";
            string redirectUri = @"yourapp://logout";

            try
            {
                WebAuthenticatorResult authResult = await WebAuthenticator.Default.AuthenticateAsync(
                    new Uri(loginUrl),
                    new Uri(redirectUri)
                );
                Current = null;
                App.Current.Quit();
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
        }

        private async Task PullProfileData()
        {
            profile = await NetworkingAPI.GetProfile();
        }

        private async Task get_weather_forecast()
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/Prod/weather/forecast?location=adelaide";
            HttpClient httpClient = new HttpClient();
            httpClient.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token?.id_token);

            HttpResponseMessage response = await httpClient.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                Debug.Print(await response.Content.ReadAsStringAsync());
                return;
            }
        }

        public static Account? Current { get; set; }

        public static async Task Initialize()
        {
            string? authCode = await TryGetAuthCodeAsync();
            if (authCode == null)
            {
                throw new NullReferenceException("authCode is null.");
            }

            Token? token = await TryGetTokenAsync("6s89mphvvhjr5lt7es4v0ap55q", "authorization_code", authCode);
            if (token == null)
            {
                throw new Exception("Failed to retrieve ID token.");
            }
            Current = new Account(token);
            await Current.PullProfileData();

            if (Current.profile == null || string.IsNullOrEmpty(Current.profile.user_id))
            {
                ContentPage? currentPage = Helpers.NavigationHelper.GetCurrentContentPage();
                if (currentPage == null)
                {
                    throw new NullReferenceException("currentPage is null.");
                }
                await currentPage.Navigation.PushModalAsync(new Pages.WelcomingPage());
            }
        }

        private static async Task<string?> TryGetAuthCodeAsync()
        {
            //string loginUrl = @"https://livewell.auth.us-east-1.amazoncognito.com/login?client_id=6s89mphvvhjr5lt7es4v0ap55q&response_type=code&scope=email+openid+phone+profile&redirect_uri=yourapp%3A%2F%2Fauth";
            string loginUrl = @"https://livewell.auth.us-east-1.amazoncognito.com/oauth2/authorize?client_id=6s89mphvvhjr5lt7es4v0ap55q&response_type=code&scope=email+openid+profile&redirect_uri=yourapp%3A%2F%2Fauth";
            string redirectUri = @"yourapp://auth";

            try
            {
                WebAuthenticatorResult authResult = await WebAuthenticator.Default.AuthenticateAsync(
                    new Uri(loginUrl),
                    new Uri(redirectUri)
                );

                string? authCode = authResult.Properties["code"];
                if (authCode == null)
                {
                    throw new NullReferenceException("authCode is null.");
                }
                return authCode;
            }
            catch (TaskCanceledException)
            {
                // User canceled the login
                App.DisplayAlert("Login Canceled", "You have canceled the login process.", "OK");
                App.Current.Quit();
                return null;
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
                App.DisplayAlert("Login Failed", ex.Message, "OK");
                App.Current.Quit();
                return null;
            }
        }

        private static async Task<Token?> TryGetTokenAsync(string clientId, string grant_type, string code)
        {
            HttpClient httpClient = new HttpClient();
            string requestUrl = @"https://livewell.auth.us-east-1.amazoncognito.com/oauth2/token";

            HttpContent content = new FormUrlEncodedContent(new Dictionary<string, string>
            {
                { "grant_type", grant_type },
                { "client_id", clientId },
                { "code", code },
                { "redirect_uri", @"yourapp://auth" }
            });

            try
            {
                HttpResponseMessage response = await httpClient.PostAsync(requestUrl, content);

                if (!response.IsSuccessStatusCode)
                {
                    Debug.Print(await response.Content.ReadAsStringAsync());
                    return null;
                }
                Token? token = await response.Content.ReadFromJsonAsync<Token>();
                if (token == null)
                {
                    throw new NullReferenceException("token is null.");
                }

                Thread refreshToken_thread = new Thread(async () =>
                {
                    Thread.Sleep((token.expires_in - 10) * 1000);
                    Token? newToken = await TryGetTokenAsync("6s89mphvvhjr5lt7es4v0ap55q", "refresh_token", token.refresh_token);
                    if (newToken == null)
                    {
                        throw new Exception("Failed to retrieve ID token.");
                    }
                    token = newToken;
                });

                return token;
            }
            catch (Exception ex)
            {
                Debug.Print(ex.Message);
                return null;
            }
        }
    }
}
