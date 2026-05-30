using LiveWell.Models;
using LiveWell.Networking;

namespace LiveWell.Pages;

public partial class EditPlanPage : ContentPage
{
	Plan? _plan;

	public EditPlanPage()
	{
        InitializeComponent();
		Title = "New Plan";
    }
    public EditPlanPage(string action_type)
    {
        InitializeComponent();
        Loaded += async (s, e) =>
        {
            LoadingIndicator.IsVisible = true;
            try
            {
                Plan? new_plan = await NetworkingAPI.GenerateAACTTPlan(action_type);
                if (new_plan is null)
                {
                    throw new Exception("Failed to generate AI plan.");
                }
                ImportPlanData(new_plan);
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", ex.Message, "OK");
            }
            LoadingIndicator.IsVisible = false;
        };
    }
    public EditPlanPage(Plan plan)
    {
        _plan = plan;
        InitializeComponent();
        BtnDelete.IsVisible = true;
        StatusLayout.IsVisible = true;
        if (plan.status == "active")
        {
            StatusLabel.Text = "Active";
            StatusSwitch.IsToggled = true;
        }
        else
        {
            StatusLabel.Text = "Inactive";
            StatusSwitch.IsToggled = false;
        }

        ImportPlanData(plan);
    }

    private void ImportPlanData(Plan plan)
    {
        try
        {
            EntryName.Text = plan.action.name;
            EditorDescription.Text = plan.action.description;
            EntryLocation.Text = plan.context.location;
            EntryCondition.Text = plan.context.condition;
            EntryTarget.Text = plan.target;
            EntryFrequencyValue.Text = plan.time.frequency.value.ToString();
            EntryFrequencyUnit.Text = plan.time.frequency.unit;
            EntryDurationValue.Text = plan.time.duration.value.ToString();
            EntryDurationUnit.Text = plan.time.duration.unit;
        }
        catch (Exception)
        {
            DisplayAlert("Error", "One or more fields are empty.", "OK");
        }
    }

    private async void BtnSave_Clicked(object sender, EventArgs e)
    {
        if (string.IsNullOrWhiteSpace(EntryName.Text) ||
            string.IsNullOrWhiteSpace(EditorDescription.Text) ||
            string.IsNullOrWhiteSpace(EntryLocation.Text) ||
            string.IsNullOrWhiteSpace(EntryCondition.Text) ||
            string.IsNullOrWhiteSpace(EntryTarget.Text) ||
            string.IsNullOrWhiteSpace(EntryFrequencyValue.Text) ||
            string.IsNullOrWhiteSpace(EntryFrequencyUnit.Text) ||
            string.IsNullOrWhiteSpace(EntryDurationValue.Text) ||
            string.IsNullOrWhiteSpace(EntryDurationUnit.Text))
        {
            await DisplayAlert("Validation Error", "Please fill all available fields", "OK");
            return;
        }

        LoadingIndicator.IsVisible = true;
        try
        {
            Plan new_plan = new Plan()
            {
                plan_type = "manually_created",
                action = new Plan.Action()
                {
                    name = EntryName.Text,
                    action_type = "N/A",
                    description = EditorDescription.Text,
                },
                actor = "user",
                context = new Plan.Context()
                {
                    location = EntryLocation.Text,
                    condition = EntryCondition.Text,
                },
                target = EntryTarget.Text,
                time = new Plan.Time()
                {
                    frequency = new Plan.Time.Frequency()
                    {
                        value = int.TryParse(EntryFrequencyValue.Text, out int freqValue) ? freqValue : 0,
                        unit = EntryFrequencyUnit.Text,
                    },
                    duration = new Plan.Time.Duration()
                    {
                        value = int.TryParse(EntryDurationValue.Text, out int durValue) ? durValue : 0,
                        unit = EntryDurationUnit.Text,
                    }
                }
            };

            if (_plan != null)
            {
                new_plan.plan_id = _plan.plan_id;
                string plan_status = StatusSwitch.IsToggled ? "active" : "inactive";
                if (_plan.status != plan_status)
                {
                    await NetworkingAPI.UpdatePlan(new_plan.plan_id!, StatusSwitch.IsToggled);
                }
                await NetworkingAPI.UpdatePlan(new_plan);
            }
            else
            {
                await NetworkingAPI.SaveNewPlan(new_plan);
            }

            await Navigation.PopAsync();
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", ex.Message, "OK");
        }
        LoadingIndicator.IsVisible = false;
    }

    private async void BtnDelete_Clicked(object sender, EventArgs e)
    {
        if (_plan == null) return;

        bool confirm = await DisplayAlert("Delete Plan", "Are you sure you want to delete this plan?", "Yes", "No");
        if (!confirm) return;

        LoadingIndicator.IsVisible = true;
        try
        {
            await NetworkingAPI.DeletePlan(_plan.plan_id);
            await Navigation.PopAsync();
        }
        catch (Exception ex)
        {
            await DisplayAlert("Error", ex.Message, "OK");
        }
        LoadingIndicator.IsVisible = false;
    }
}