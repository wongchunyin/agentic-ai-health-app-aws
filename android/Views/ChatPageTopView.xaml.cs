using LiveWell.Models;
using LiveWell.Networking;
using LiveWell.Pages;

namespace LiveWell.Views;

public partial class ChatPageTopView : ContentView
{
    ChatPage chatPage;
    List<AgentConversation>? sessions;
    string? currentSessionId = null;

    public ChatPageTopView(ChatPage chatPage)
	{
		InitializeComponent();
        this.chatPage = chatPage;

        Loaded += async (s, e) =>
        {
            try
            {
                sessions = await NetworkingAPI.GetChatHistory();

                if (sessions is null)
                    return;
                foreach (var conversation in sessions)
                {
                    SessionPicker.Items.Add(conversation.chat_session_name!);
                }
                SessionPicker.SelectedItem = null;
            }
            catch (Exception ex)
            {
                App.DisplayAlert("Error", ex.Message, "OK");
            }
        };
    }

    public void UpdateSessionId(string sessionId)
    {
        if (currentSessionId is not null)
            return;
        currentSessionId = sessionId;
    }

    private void SessionPicker_SelectedIndexChanged(object sender, EventArgs e)
    {
        var senderPicker = sender as Picker;
        if (senderPicker is null || senderPicker.SelectedItem is null)
        {
            return;
        }

        try
        {
            chatPage.MessagesLayout.Clear();
            if (sessions is null)
                throw new NullReferenceException("Cannot get session's information.");

            AgentConversation? conversation = sessions.Find(c => c.chat_session_name == SessionPicker.SelectedItem as string);
            if (conversation is null)
                throw new NullReferenceException("Cannot get selected session's information.");
            currentSessionId = conversation.conversation_id;
            foreach (var message in conversation.messages!)
            {
                if (message.role == "user")
                {
                    chatPage.ShowUserMessage(message.content!);
                }
                else
                {
                    chatPage.ShowAgentResponse(message.content!);
                }
            }
        }
        catch (Exception ex)
        {
            chatPage.DisplayAlert("Error", ex.Message, "OK");
        }
    }

    private void NewSessionButton_Clicked(object sender, EventArgs e)
    {
        try
        {
            chatPage.MessagesLayout.Clear();
            currentSessionId = null;
            SessionPicker.Title = "New Chat Session";
            SessionPicker.SelectedItem = null;
        }
        catch (Exception ex)
        {
            App.DisplayAlert("Error", ex.Message, "OK");
        }
    }

    private void RenameSessionButton_Clicked(object sender, EventArgs e)
    {
        try
        {
            SessionPicker.IsVisible = false;
            SessionNameEntry.IsVisible = true;
            SessionNameEntry.Text = SessionPicker.SelectedItem as string;
            RenameSessionButton.IsVisible = false;
            AcceptRenameButton.IsVisible = true;
        }
        catch (Exception ex)
        {
            App.DisplayAlert("Error", ex.Message, "OK");
        }
    }

    private void AcceptRenameButton_Clicked(object sender, EventArgs e)
    {
        try
        {
            RenameSessionButton.IsVisible = true;
            AcceptRenameButton.IsVisible = false;
            SessionPicker.IsVisible = true;
            SessionNameEntry.IsVisible = false;

            if (SessionNameEntry.Text != null && SessionNameEntry.Text != string.Empty)
            {
                if (SessionPicker.SelectedItem is null)
                    SessionPicker.Items.Add(SessionNameEntry.Text);
                else
                    SessionPicker.Items[SessionPicker.SelectedIndex] = SessionNameEntry.Text;
                SessionPicker.SelectedItem = SessionNameEntry.Text;
                if (sessions is not null)
                {
                    var conversation = sessions.Find(c => c.conversation_id == currentSessionId);
                    if (conversation is not null)
                    {
                        conversation.chat_session_name = SessionNameEntry.Text;
                        //NetworkingAPI.RenameChatSession(conversation).Wait();
                    }
                }
            }
        }
        catch (Exception ex)
        {
            App.DisplayAlert("Error", ex.Message, "OK");
        }
    }

    private async void DeleteSessionButton_Clicked(object sender, EventArgs e)
    {
        try
        {
            bool confirm = await chatPage.DisplayAlert("Warning",
        "Are you sure you want to delete this chat session? This action cannot be undone.",
        "Yes", "No");
            if (!confirm)
            {
                return;
            }
            if (sessions is not null)
            {
                var conversation = sessions.Find(c => c.conversation_id == currentSessionId);
                if (conversation is not null)
                {
                    await NetworkingAPI.RemoveChatHistory(currentSessionId!);
                    sessions.Remove(conversation);
                }
            }
            NewSessionButton_Clicked(sender, e);
        }
        catch (Exception ex)
        {
            App.DisplayAlert("Error", ex.Message, "OK");
        }
    }
}