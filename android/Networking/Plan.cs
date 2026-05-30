using Java.Util;
using LiveWell.Models;
using System.Net.Http.Json;
using System.Text.Json;

namespace LiveWell.Networking
{
    public static partial class NetworkingAPI
    {
        public static async Task<List<Plan>?> GetPlan()
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans?all=true";

            SetAuthorizationHeader();
            HttpResponseMessage response = await client.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to get plan. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("plans"))
            {
                throw new Exception("Invalid response from server.");
            }
            List<Plan>? plans = JsonSerializer.Deserialize<List<Plan>>(responseJson["plans"].ToString()!);
            return plans;
        }
        public static async Task<Plan?> GetPlan(string plan_id)
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans/{plan_id}";

            SetAuthorizationHeader();
            HttpResponseMessage response = await client.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to get plan. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("plan"))
            {
                throw new Exception("Invalid response from server.");
            }
            Plan? plan = JsonSerializer.Deserialize<Plan>(responseJson["plan"].ToString()!);
            return plan;
        }

        public static async Task DeletePlan(string plan_id)
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans/{plan_id}";

            SetAuthorizationHeader();
            HttpResponseMessage response = await client.DeleteAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to delete plan. Status code: {response.StatusCode}");
            }
        }

        public static async Task SaveNewPlan(Plan plan)
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans";
            
            Dictionary<string, object> contentDict = new Dictionary<string, object>
            {
                { "plan_data", plan }
            };
            JsonContent content = JsonContent.Create(contentDict, options: IgnoreWritingNullOption);

            SetAuthorizationHeader();
            HttpResponseMessage response = await client.PostAsync(requestUrl, content);
            if (!response.IsSuccessStatusCode)
            {
                if (response.StatusCode == System.Net.HttpStatusCode.BadRequest)
                {
                    var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
                    if (responseJson != null)
                    {
                        throw new Exception(responseJson["reason"].ToString()!);
                    }
                }
                throw new Exception($"Failed to save plan. Status code: {response.StatusCode}");
            }
        }

        public static async Task<Plan?> GenerateAACTTPlan(string action_type)
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/aactt/generate";
            StringContent content = new StringContent(
                JsonSerializer.Serialize(new { action_type = action_type }),
                System.Text.Encoding.UTF8,
                "application/json");
            
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.PostAsync(requestUrl, content);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to generate plan. Status code: {response.StatusCode}");
            }
            Plan? plan = await response.Content.ReadFromJsonAsync<Plan>();
            return plan;
        }

        public static async Task<Plan> UpdatePlan(Plan plan)
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans/{plan.plan_id}";
            JsonContent content = JsonContent.Create(plan, options: IgnoreWritingNullOption);
            
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.PatchAsync(requestUrl, content);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to update plan. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("plan_data"))
            {
                throw new Exception("Invalid response from server.");
            }
            Plan? updated_plan = JsonSerializer.Deserialize<Plan>(responseJson["plan_data"].ToString()!);
            return updated_plan!;
        }
        public static async Task UpdatePlan(string plan_id, bool is_active)
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans/{plan_id}";
            string status = is_active ? "active" : "inactive";
            Dictionary<string, string> update = new Dictionary<string, string>
            {
                { "status", status }
                // active inactive completed canceled
            };
            JsonContent content = JsonContent.Create(update, options: IgnoreWritingNullOption);

            SetAuthorizationHeader();
            HttpResponseMessage response = await client.PatchAsync(requestUrl, content);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to update plan. Status code: {response.StatusCode}");
            }
        }
    }
}
