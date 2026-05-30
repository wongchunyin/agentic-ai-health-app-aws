using LiveWell.Models;
using LiveWell.Networking;
using System.Text.Json;

namespace LiveWell.Views;

public partial class PlanView : ContentView
{
	Plan plan;
	public PlanView(Plan plan)
	{
		this.plan = plan;
        InitializeComponent();

        Loaded += async (s, e) =>
        {
            await LoadPlanData();
            CheckBoxCompleted.CheckedChanged += CheckBoxCompleted_CheckedChanged;
        };
    }

	private async Task LoadPlanData()
	{
        try
        {
            LabelName.Text = plan.action.name;
            LabelAction.Text = plan.action.description;
            LabelContext.Text = $"{plan.context.location}, {plan.context.condition}";
            LabelTarget.Text = plan.target;
            LabelTime.Text = $"{plan.time.frequency.value} {plan.time.frequency.unit}, {plan.time.duration.value} {plan.time.duration.unit}";
            LabelFrequency.Text = $"{plan.time.frequency.value} {plan.time.frequency.unit}";

            if (Account.Current!.schedule_tasks is null || plan.status is null || plan.status == "inactive")
            {
                LabelStatus.Text = "Disabled";
                LabelFrequency.IsVisible = false;
                CheckBoxCompleted.IsVisible = false;
                return;
            }


            var task = Account.Current!.schedule_tasks?.Find(task =>
                task.plan_id == plan.plan_id
            );
            if (task is null)
            {
                LabelStatus.Text = "Disabled";
                LabelFrequency.IsVisible = false;
                CheckBoxCompleted.IsVisible = false;
                return;
            }
            if (task.cnt_activity_done >= task.target)
            {
                CheckBoxCompleted.IsChecked = true;
                LabelStatus.Text = "Completed for this cycle";
                CheckBoxCompleted.IsEnabled = false;
            }
            else
            {
                CheckBoxCompleted.IsChecked = false;
                LabelStatus.Text = $"{task.cnt_activity_done} / {task.target} completed";
            }
        }
        catch (Exception ex)
        {
            App.DisplayAlert("Error", ex.Message, "OK");
        }
    }

    private void BtnEdit_Clicked(object sender, EventArgs e)
    {
        try
        {
            Navigation.PushAsync(new Pages.EditPlanPage(plan));
        }
        catch (Exception ex)
        {
            App.DisplayAlert("Error", ex.Message, "OK");
        }
    }

    private async void CheckBoxCompleted_CheckedChanged(object? sender, CheckedChangedEventArgs e)
    {
        try
        {
            if (CheckBoxCompleted.IsChecked)
            {
                await NetworkingAPI.RecordActivityDone(plan.plan_id!);
                MainPage? mainPage = App.GetCurrentPage() as MainPage;
                if (mainPage == null)
                {
                    throw new Exception("Unable to update Dashboard");
                }
                await mainPage.UpdatePage();
            }
        }
        catch (Exception ex)
        {
            App.DisplayAlert("Error", ex.Message, "OK");
        }
    }
}