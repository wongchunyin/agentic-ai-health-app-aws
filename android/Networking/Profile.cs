using LiveWell.Models;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;

namespace LiveWell.Networking
{
    public static partial class NetworkingAPI
    {
        public static async Task<Profile?> GetProfile()
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/profile";
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                return null;
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("profile"))
            {
                return null;
            }
            Profile? profile = JsonSerializer.Deserialize<Profile>(responseJson["profile"].ToString()!);
            return profile;
        }

        public static async Task<Profile?> SaveProfile(Profile profile)
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/profile";
            SetAuthorizationHeader();
            HttpContent content = JsonContent.Create(profile, options: IgnoreWritingNullOption);

            HttpResponseMessage response = await client.PostAsync(requestUrl, content);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to save profile. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("profile"))
            {
                throw new Exception("Invalid response from server.");
            }
            Profile? saved_profile = JsonSerializer.Deserialize<Profile>(responseJson["profile"].ToString()!);
            return saved_profile;
        }

        public static async Task<Profile?> UpdateProfile(Profile profile)
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/profile";
            SetAuthorizationHeader();
            HttpContent content = JsonContent.Create(profile, options: IgnoreWritingNullOption);
            HttpResponseMessage response = await client.PutAsync(requestUrl, content);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to update profile. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("profile"))
            {
                throw new Exception("Invalid response from server.");
            }
            Profile? updated_profile = JsonSerializer.Deserialize<Profile>(responseJson["profile"].ToString()!);
            return updated_profile;
        }
    }
}
