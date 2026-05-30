namespace LiveWell.Views;

public partial class FrailtyHistoryView : ContentView
{
	public FrailtyHistoryView(string date, double score, string scale)
	{
		InitializeComponent();
		DateLabel.Text = date;
		ScoreLabel.Text = score.ToString();
		ScaleLabel.Text = scale;

        if (scale.Equals("FRAIL"))
        {
            if (score < 2)
            {
                ScoreLabel.TextColor = Colors.Green;
            }
            else if (score >= 2 && score <= 3)
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
            if (score < 0.4)
            {
                ScoreLabel.TextColor = Colors.Green;
            }
            else if (score >= 0.4 && score <= 0.7)
            {
                ScoreLabel.TextColor = Colors.Orange;
            }
            else
            {
                ScoreLabel.TextColor = Colors.Red;
            }
        }
    }
}