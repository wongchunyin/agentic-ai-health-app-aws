namespace LiveWell.Views;

public partial class ChatBox : ContentView
{
	public ChatBox()
	{
		InitializeComponent();
	}
    public ChatBox(string message, bool isUser)
    {
        InitializeComponent();
        MessageLabel.Text = message;
        if (isUser)
        {
            HorizontalOptions = LayoutOptions.End;
            MessageLabel.TextColor = Colors.White;
            var hasValue = Application.Current!.Resources.TryGetValue("Primary", out object primaryColor);
            if (hasValue)
            {
                MessageFrame.BackgroundColor = (Color)primaryColor;
            }
        }
    }
}