using Android.App;
using Android.Content;
using Android.Content.PM;

namespace LiveWell.Platforms.Android
{
    [Activity(NoHistory = true, LaunchMode = LaunchMode.SingleTop, Exported = true)]
    [IntentFilter([Intent.ActionView],
              Categories = new[] { Intent.CategoryDefault, Intent.CategoryBrowsable },
              DataScheme = "yourapp", DataHosts = new[] { "auth", "logout" })]
    internal class WebAuthenticatorCallbackActivity : Microsoft.Maui.Authentication.WebAuthenticatorCallbackActivity
    {
    }
}
