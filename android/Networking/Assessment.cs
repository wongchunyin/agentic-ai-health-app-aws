using LiveWell.Models;
using System.Net.Http.Json;
using System.Text.Json;

namespace LiveWell.Networking
{
    public partial class NetworkingAPI
    {
        public static async Task<List<FrailtyAssessment>?> GetAssessmentHistory()
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments/all?status=completed";
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to get assessment history. Status code: {response.StatusCode}");
            }
            var assessments = await response.Content.ReadFromJsonAsync<List<FrailtyAssessment>>();
            if (assessments == null)
            {
                throw new Exception("Invalid response from server.");
            }
            return assessments;
        }

        public static async Task<FrailtyAssessment?> SaveNewAssessment(FrailtyAssessment assessment)
        {
            string requestUrl = @"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments";
            SetAuthorizationHeader();
            HttpContent content = JsonContent.Create(assessment, options: IgnoreWritingNullOption);
            HttpResponseMessage response = await client.PostAsync(requestUrl, content);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to save assessment. Status code: {response.StatusCode}");
            }
            var responseJson = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>();
            if (responseJson == null || !responseJson.ContainsKey("assessment_result"))
            {
                throw new Exception("Invalid response from server.");
            }
            assessment.assessment_id = responseJson["assessment_id"].ToString()!;
            assessment.result = JsonSerializer.Deserialize<FrailtyAssessment.FrailtyResult>(responseJson["assessment_result"].ToString()!);
            return assessment;
        }

        public static async Task<JsonDocument?> GetAssessmentQuestion(string assessment_type)
        {
            string requestUrl = $"https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments/questions/{assessment_type}";
            SetAuthorizationHeader();
            HttpResponseMessage response = await client.GetAsync(requestUrl);
            if (!response.IsSuccessStatusCode)
            {
                throw new Exception($"Failed to get assessment questions. Status code: {response.StatusCode}");
            }
            var jsonDoc = await response.Content.ReadFromJsonAsync<JsonDocument>();
            if (jsonDoc == null)
            {
                throw new Exception("Invalid response from server.");
            }
            return jsonDoc;
        }
    }
}
