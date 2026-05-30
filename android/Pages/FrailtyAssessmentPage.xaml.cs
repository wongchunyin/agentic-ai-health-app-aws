using LiveWell.Models;
using LiveWell.Networking;
using System.Diagnostics;
using System.Text.Json;

namespace LiveWell.Pages
{
    public partial class FrailtyAssessmentPage : ContentPage
    {
        Dictionary<string, object> assessment_data = new Dictionary<string, object>();
        public string? assessment_type = null;
        public bool completed = false;

        private List<string> illnesses = new List<string>();

        public FrailtyAssessmentPage()
        {
            InitializeComponent();
        }

        private async Task AddQuestion()
        {
            LoadingIndicator.IsVisible = true;
            if (string.IsNullOrEmpty(assessment_type))
                throw new NullReferenceException("Assessment type is null or empty.");

            JsonDocument? jsonDoc = await NetworkingAPI.GetAssessmentQuestion(assessment_type);
            if (jsonDoc is null)
            {
                throw new NullReferenceException("Cannot get assessment questions.");
            }

            foreach (var factorKey in jsonDoc.RootElement.EnumerateObject())
            {
                // Add Question
                string? question = factorKey.Value.GetProperty("question").GetString();
                string? description = factorKey.Value.GetProperty("description").GetString();
                var questionLayout = new HorizontalStackLayout();
                var questionLabel = new Label()
                {
                    Text = question,
                    FontSize = 16,
                    WidthRequest = App.GetScreenWidth() * 0.75,
                    LineBreakMode = LineBreakMode.WordWrap
                };
                var descBtn = new ImageButton()
                {
                    Source = "help_icon.png",
                    WidthRequest = 30,
                    HeightRequest = 30,
                    Scale = 0.5,
                    BackgroundColor = Colors.Transparent
                };
                descBtn.Clicked += (sender, e) =>
                {
                    DisplayAlert("Description", description, "OK");
                };
                questionLayout.Add(questionLabel);
                questionLayout.Add(descBtn);

                // Add Picker
                var optionsLayout = new VerticalStackLayout();
                if (factorKey.Name == "illnesses")
                {
                    assessment_data.Add(factorKey.Name, illnesses);
                    AddOptionsAsCheckBoxes(optionsLayout, factorKey);
                }
                else
                {
                    assessment_data.Add(factorKey.Name, 0);
                    AddOptionsAsRadioButtons(optionsLayout, factorKey);
                }

                AssessmentContentContainer.Add(questionLayout);
                AssessmentContentContainer.Add(optionsLayout);
            }
            LoadingIndicator.IsVisible = false;
        }
        private void AddOptionsAsRadioButtons(VerticalStackLayout container, JsonProperty factorKey)
        {
            foreach (var option in factorKey.Value.GetProperty("options").EnumerateArray())
            {
                object value = assessment_type == "FRAIL" ?
                    option.GetProperty("value").GetBoolean() :
                    option.GetProperty("value").GetInt32();
                string? label = option.GetProperty("label").GetString();
                var optionRadio = new RadioButton()
                {
                    Content = label,
                    Value = value,
                    FontSize = 14,
                };
                optionRadio.CheckedChanged += (sender, e) =>
                {
                    try
                    {
                        if (e.Value)
                        {
                            assessment_data[factorKey.Name] = value;
                        }
                    }
                    catch (Exception ex)
                    {
                        DisplayAlert("Error", ex.Message, "OK");
                    }
                };
                container.Add(optionRadio);
            }
        }
        private void AddOptionsAsCheckBoxes(VerticalStackLayout container, JsonProperty factorKey)
        {
            foreach (var option in factorKey.Value.GetProperty("options").EnumerateArray())
            {
                string? value = option.GetProperty("value").GetString();

                var optionCheckBoxWithLabel = new HorizontalStackLayout();
                var optionLabel = new Label()
                {
                    Text = value,
                    FontSize = 14,
                };
                var optionCheckBox = new CheckBox();
                optionCheckBox.CheckedChanged += (sender, e) =>
                {
                    try
                    {
                        if (e.Value)
                        {
                            illnesses.Add(value!);
                        }
                        else
                        {
                            illnesses.Remove(value!);
                        }
                    }
                    catch (Exception ex)
                    {
                        DisplayAlert("Error", ex.Message, "OK");
                    }
                };
                optionCheckBoxWithLabel.Add(optionCheckBox);
                optionCheckBoxWithLabel.Add(optionLabel);
                container.Add(optionCheckBoxWithLabel);
            }
        }

        private void AddCalcButton()
        {
            var calcButton = new Button()
            {
                Text = "Calculate Frailty Score",
                FontSize = 16,
                HorizontalOptions = LayoutOptions.End,
            };
            calcButton.Clicked += BtnCalc_Clicked!;
            AssessmentContentContainer.Add(calcButton);
        }

        private async void FrailtyScalePicker_SelectedIndexChanged(object sender, EventArgs e)
        {
            try
            {
                assessment_data = new Dictionary<string, object>();
                assessment_type = FrailtyScalePicker.SelectedItem.ToString();
                AssessmentContentContainer.Clear();
                await AddQuestion();
                AddCalcButton();
            }
            catch (Exception ex)
            {
                await DisplayAlert("Error", ex.Message, "OK");
                assessment_data.Clear();
                illnesses.Clear();
                AssessmentContentContainer.Clear();
            }
        }

        private async void BtnCalc_Clicked(object sender, EventArgs e)
        {
            LoadingIndicator.IsVisible = true;
            try
            {
                FrailtyAssessment? assessment = new FrailtyAssessment()
                {
                    assessment_type = assessment_type,
                    assessment_data = assessment_data,
                };
                assessment = await NetworkingAPI.SaveNewAssessment(assessment);
                if (assessment is null || assessment.result is null)
                {
                    throw new NullReferenceException("Cannot get assessment result.");
                }
                string message_result = $"Your Frailty Score is {assessment.result.score} - {assessment.result.level}\n{assessment.result.description}";
                await DisplayAlert("Assessment Completed", message_result, "OK");
                completed = true;
                await Navigation.PopAsync();
            }
            catch (Exception ex)
            {
                Debug.WriteLine(ex.Message);
                await DisplayAlert("Error", ex.Message, "OK");
                return;
            }
            LoadingIndicator.IsVisible = false;
        }
    }
}