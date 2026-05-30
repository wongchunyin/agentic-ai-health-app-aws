using System.Linq;
using Microsoft.Maui.Controls;

namespace LiveWell.Helpers
{
    public static class NavigationHelper
    {
        public static ContentPage? GetCurrentContentPage()
        {
            var main = Application.Current?.MainPage;
            if (main == null)
                return null;

            // If there are modal pages shown, the top-most modal is the visible page
            var navigation = main.Navigation;
            if (navigation?.ModalStack?.Count > 0)
            {
                var topModal = navigation.ModalStack.Last();
                return ResolveContentPage(topModal);
            }

            // Shell apps
            if (main is Shell)
            {
                return ResolveContentPage(Shell.Current?.CurrentPage);
            }

            // NavigationPage
            if (main is NavigationPage navMain)
            {
                return ResolveContentPage(navMain.CurrentPage);
            }

            // TabbedPage
            if (main is TabbedPage tabMain)
            {
                return ResolveContentPage(tabMain.CurrentPage);
            }

            // FlyoutPage (MasterDetail)
            if (main is FlyoutPage flyout)
            {
                return ResolveContentPage(flyout.Detail);
            }

            // Fallback: if MainPage itself is a ContentPage
            return ResolveContentPage(main);
        }

        private static ContentPage? ResolveContentPage(Page? page)
        {
            if (page == null)
                return null;

            // If it's a NavigationPage, return its current page
            if (page is NavigationPage np)
                page = np.CurrentPage;

            // If it's a Shell, return Shell.Current.CurrentPage
            if (page is Shell)
                page = Shell.Current?.CurrentPage;

            // If it's a TabbedPage, use CurrentPage
            if (page is TabbedPage tp)
                page = tp.CurrentPage;

            // If it's a FlyoutPage, use Detail
            if (page is FlyoutPage fp)
                page = fp.Detail;

            return page as ContentPage;
        }
    }
}