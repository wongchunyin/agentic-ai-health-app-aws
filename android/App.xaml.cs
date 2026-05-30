using LiveWell.Helpers;

namespace LiveWell
{
    public partial class App : Application
    {
        public App()
        {
            InitializeComponent();
            UserAppTheme = AppTheme.Light;
        }

        protected override Window CreateWindow(IActivationState? activationState)
        {
            return new Window(new AppShell());
        }

        public static ContentPage? GetCurrentPage()
        {
            return NavigationHelper.GetCurrentContentPage();
        }
        public static void DisplayAlert(string title, string message, string btnText)
        {
            var currentPage = GetCurrentPage();
            if (currentPage != null)
            {
                currentPage.DisplayAlert(title, message, btnText);
            }
        }

        public static double GetScreenWidth() => DeviceDisplay.MainDisplayInfo.Width / DeviceDisplay.MainDisplayInfo.Density;
        public static double GetScreenHeight() => DeviceDisplay.MainDisplayInfo.Height / DeviceDisplay.MainDisplayInfo.Density;
    }
}