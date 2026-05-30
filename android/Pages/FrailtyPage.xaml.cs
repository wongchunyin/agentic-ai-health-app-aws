using LiveWell.Models;
using LiveWell.Views;
using LiveWell.Networking;

namespace LiveWell.Pages;

public partial class FrailtyPage : ContentPage
{
    List<FrailtyAssessment>? assessments;

	public FrailtyPage()
	{
        InitializeComponent();
        NavigatedTo += async (e, args) => await UpdatePage();
    }

    private async Task UpdatePage()
    {
        LoadingIndicator.IsVisible = true;
        try
        {
            assessments = await NetworkingAPI.GetAssessmentHistory();
            if (assessments == null || assessments.Count == 0)
            {
                FrailtyListLayout.IsVisible = false;
                EmptyLayout.IsVisible = true;
                return;
            }
            assessments = assessments
                .OrderByDescending(a => DateTime.Parse(a.timestamp!))
                .ToList();

            EmptyLayout.IsVisible = false;
            FrailtyListLayout.IsVisible = true;

            ScoreLabel.Text = assessments?[0].score.ToString();
            ScaleLabel.Text = assessments?[0].assessment_type;
            DateLabel.Text = DateTime.Parse(assessments?[0].timestamp!).ToString();

            if (assessments![0].assessment_type!.Equals("FRAIL"))
            {
                if (assessments[0].score < 2)
                {
                    ScoreLabel.TextColor = Colors.Green;
                }
                else if (assessments[0].score >= 2 && assessments[0].score <= 3)
                {
                    ScoreLabel.TextColor = Colors.Orange;
                }
                else
                {
                    ScoreLabel.TextColor = Colors.Red;
                }
            }
            else
            {
                if (assessments[0].score < 0.4)
                {
                    ScoreLabel.TextColor = Colors.Green;
                }
                else if (assessments[0].score >= 0.4 && assessments[0].score <= 0.7)
                {
                    ScoreLabel.TextColor = Colors.Orange;
                }
                else
                {
                    ScoreLabel.TextColor = Colors.Red;
                }
            }

            HistoryStackLayout.Clear();
            foreach (var assessment in assessments)
            {
                FrailtyHistoryView view = new FrailtyHistoryView(
                    DateTime.Parse(assessment.timestamp!).ToString(),
                    (double)assessment.score!,
                    assessment.assessment_type!);
                HistoryStackLayout.Add(view);
            }
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", ex.Message, "OK");
        }
        LoadingIndicator.IsVisible = false;
    }

    private async void Button_Clicked(object sender, EventArgs e)
    {
        try
        {
            FrailtyAssessmentPage assessmentPage = new FrailtyAssessmentPage();
            assessmentPage.Disappearing += async (s, args) =>
            {
                if (assessmentPage.completed)
                {
                    await UpdatePage();
                }
            };
            await Navigation.PushAsync(assessmentPage);
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", ex.Message, "OK");
        }
    }
}