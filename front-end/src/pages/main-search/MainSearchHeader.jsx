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
              { text: "Vistsco", href: "#" },
              { text: "知识库", href: "#" },
            ]}
            ariaLabel="知识库"
          />
          <SpaceBetween size="m">
            <Header variant="h1" description="请在下方输入您的问题并做筛选">
              知识库
            </Header>
          </SpaceBetween>
        </>
      }
    >
      <Container
        header={
          <Header variant="h2" description="请在此处输入您的问题描述">
            问题描述
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
