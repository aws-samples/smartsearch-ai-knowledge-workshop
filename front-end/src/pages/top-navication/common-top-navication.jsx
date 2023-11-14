import * as React from "react";
import TopNavigation from "@cloudscape-design/components/top-navigation";

const CommonTopNav = () => {
  const i18nStrings = {
    searchIconAriaLabel: "Search",
    searchDismissIconAriaLabel: "Close search",
    overflowMenuTriggerText: "More",
    overflowMenuTitleText: "All",
    overflowMenuBackIconAriaLabel: "Back",
    overflowMenuDismissIconAriaLabel: "Close menu",
  };
  return (
    <TopNavigation
      i18nStrings={i18nStrings}
      identity={{
        href: "#",
        title: "Smart Search Knowledge",
      }}
      utilities={[
        {
          type: "menu-dropdown",
          text: "Customer Name",
          description: "email@example.com",
          iconName: "user-profile",
          items: [],
        },
      ]}
    />
  );
};
export default CommonTopNav;
