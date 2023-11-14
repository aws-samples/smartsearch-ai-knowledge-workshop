import * as React from "react";
import ContentLayout from "@cloudscape-design/components/content-layout";
import Container from "@cloudscape-design/components/container";
import Header from "@cloudscape-design/components/header";
import SpaceBetween from "@cloudscape-design/components/space-between";
import BreadcrumbGroup from "@cloudscape-design/components/breadcrumb-group";
import MainSearchTable from "./MainSearchTable";

const MainSearchHeader = ({
  setQuery,
  setNewItems,
  btnLoading,
  setBtnLoading,
}) => {
  return (
    <ContentLayout
      header={
        <>
          <BreadcrumbGroup
            items={[
              { text: "Smart Search", href: "#" },
              { text: "Knowledge", href: "#" },
            ]}
            ariaLabel="Knowledge"
          />
          <SpaceBetween size="m">
            <Header variant="h1" description="A smart search and LLM knowledge">
              Knowledge
            </Header>
          </SpaceBetween>
        </>
      }
    >
      <Container
        header={
          <Header variant="h2" description="Please input your question">
            Question
          </Header>
        }
      >
        <MainSearchTable
          setQuery={setQuery}
          setNewItems={setNewItems}
          btnLoading={btnLoading}
          setBtnLoading={setBtnLoading}
        />
      </Container>
    </ContentLayout>
  );
};

export default MainSearchHeader;
