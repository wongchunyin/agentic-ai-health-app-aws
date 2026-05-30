using LiveWell.Networking;
using LiveWell.Views;

namespace LiveWell.Pages;

public partial class ChatPage : ContentPage
{
    AgentHttpClient agentClient = new();
    ChatPageTopView topView;

    public ChatPage()
	{
		InitializeComponent();
        topView = new ChatPageTopView(this);
        TopViewContainer.Add(topView);
        scrollView.MaximumHeightRequest = getScreenHeight() * 0.65;
    }

    private async void SendButton_Clicked(object sender, EventArgs e)
    {
        try
        {
            if (MessageTextBox.Text != string.Empty)
            {
                string sentMessage = MessageTextBox.Text;
                MessageTextBox.Text = string.Empty;

                ShowUserMessage(sentMessage);
                await scrollView.ScrollToAsync(0, MessagesLayout.Height, true);
                SendingIndicator.IsVisible = true;
                SendButton.IsEnabled = false;

                var agentResponse = await agentClient.GetAgentResponse(sentMessage);
                if (agentResponse == null)
                {
                    ShowAgentResponse("Sorry, I couldn't process your request at the moment.");
                }
                else
                {
                    ShowAgentResponse(agentResponse.response);
                }
                await scrollView.ScrollToAsync(0, MessagesLayout.Height, true);
                SendingIndicator.IsVisible = false;
                SendButton.IsEnabled = true;

                if (agentResponse is not null)
                {
                    topView.UpdateSessionId(agentResponse!.chat_session_id);
                }
            }
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", ex.Message, "OK");
        }
    }

    public void ShowUserMessage(string message)
    {
        PlaceholderLabel.IsVisible = false;
        MessagesLayout.Add(new ChatBox(message, true));
    }
    public void ShowAgentResponse(string response)
    {
        MessagesLayout.Add(new ChatBox(response, false));
    }

    private double getScreenHeight() => DeviceDisplay.MainDisplayInfo.Height / DeviceDisplay.MainDisplayInfo.Density;
}