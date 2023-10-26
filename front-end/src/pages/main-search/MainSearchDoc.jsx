import React, { useEffect, useState, useRef } from "react";
import { useCollection } from "@cloudscape-design/collection-hooks";
import { DEFAULT_PREFERENCES, Preferences } from "../common/table-config-doc";
import {
  Table,
  TextFilter,
  Alert,
  SpaceBetween,
  Button,
  Grid,
  Box,
  FormField,
} from "@cloudscape-design/components";
import {
  CustomAppLayout,
  TableNoMatchState,
} from "../common/common-components";
import {
  distributionSelectionLabels,
  addColumnSortLabels,
} from "../../tools/labels";
import { getFilterCounterText } from "../../tools/tableCounterStrings";
import { useColumnWidths } from "../../hooks/use-column-widths";
import { useLocalStorage } from "../../hooks/localStorage";
import MainSearchHeader from "./MainSearchHeader";
import FullPageHeader from "./FullPageHeader";
import { POST_HEADERS, SUMMARIZE_API } from "../../tools/constants";

const COLUMN_DEFINITIONS = addColumnSortLabels([
  {
    id: "id",
    sortingField: "id",
    header: "ID",
    cell: (item) => item.id,
  },
  {
    id: "question",
    sortingField: "question",
    header: "问题",
    cell: (item) => item.question,
    minWidth: 180,
  },

  {
    id: "answers",
    sortingField: "answers",
    header: "分析与处理",
    cell: (item) => (
      <div
        dangerouslySetInnerHTML={{
          __html: item.answers?.replaceAll("\n", "<br>"),
        }}
      ></div>
    ),
    minWidth: 280,
  },
  {
    id: "machinetypename",
    sortingField: "machinetypename",
    header: "工艺名称",
    cell: (item) => item.machinetypename,
  },
  {
    id: "linename",
    sortingField: "linename",
    header: "流水线",
    cell: (item) => item.linename,
    minWidth: 220,
  },
  {
    id: "manufacturing_process_number",
    sortingField: "manufacturing_process_number",
    header: "工艺号",
    cell: (item) => item.manufacturing_process_number,
  },
  {
    id: "reply_upload_file",
    sortingField: "reply_upload_file",
    header: "相关手册",
    cell: (item) => item.reply_upload_file,
    minWidth: 200,
  },
  {
    id: "action_des",
    sortingField: "action_des",
    cell: (item) => item.action_des,
    header: "处理方式",
  },
  {
    id: "root_cause_des",
    sortingField: "root_cause_des",
    header: "根本原因",
    cell: (item) => item.root_cause_des,
  },
  {
    id: "upload_date",
    sortingField: "upload_date",
    header: "更新日期",
    cell: (item) => item.upload_date,
  },
  {
    id: "problemid",
    sortingField: "problemid",
    header: "问题ID",
    cell: (item) => item.problemid,
  },
  {
    id: "linekey",
    sortingField: "linekey",
    header: "流水线ID",
    cell: (item) => item.linekey,
  },
  {
    id: "machinekey",
    sortingField: "machinekey",
    header: "设备ID",
    cell: (item) => item.machinekey,
  },
  {
    id: "action_linkid",
    sortingField: "action_linkid",
    header: "处理方式Id",
    cell: (item) => item.action_linkid,
  },
  {
    id: "root_causeid",
    sortingField: "root_causeid",
    header: "根本原因ID",
    cell: (item) => item.root_causeid,
  },
  {
    id: "machinetypekey",
    sortingField: "machinetypekey",
    header: "工艺号ID",
    cell: (item) => item.machinetypekey,
  },
]);

function TableContent({ distributions, updateTools }) {
  const [columnDefinitions, saveWidths] = useColumnWidths(
    "React-Table-Widths",
    COLUMN_DEFINITIONS
  );
  const [preferences, setPreferences] = useLocalStorage(
    "React-DistributionsTable-Preferences",
    DEFAULT_PREFERENCES
  );
  const [new_items, setNewItems] = useState([]);

  const [answerMsg, setAnswerMsg] = useState("");
  const [query, setQuery] = useState("");

  const [isFilterLoading, setIsFilterLoading] = useState(false);
  const [tableSortingField, setTableSortingField] = useState("");
  const [isDesc, setIsDesc] = useState(false);
  const [btnLoading, setBtnLoading] = useState(false);
  const [selectedItems, setSelectedItems] = useState(new_items);
  const stopConversationRef = useRef(false);

  const controller = new AbortController();
  const { signal } = controller;

  const { items, actions, filteredItemsCount, collectionProps, filterProps } =
    useCollection(new_items, {
      filtering: {
        noMatch: (
          <TableNoMatchState onClearFilter={() => actions.setFiltering()} />
        ),
        filteringFunction: (rowItem, filteringText) => {
          if (!filteringText) {
            return true;
          }
          if (!rowItem) {
            return false;
          }
          const filteringTextList = filteringText.split(" ").filter((i) => !!i);
          const itemKeyList = Object.keys(rowItem);
          if (!itemKeyList || itemKeyList.length === 0) {
            return false;
          }
          // 每列字段执行查找匹配
          for (let m = 0; m < itemKeyList.length; m++) {
            for (let n = 0; n < filteringTextList.length; n++) {
              const tempTestData = rowItem[itemKeyList[m]]
                ? rowItem[itemKeyList[m]].toString().toUpperCase()
                : "";
              if (tempTestData.includes(filteringTextList[n].toUpperCase())) {
                return true;
              }
            }
          }
          return false;
        },
      },
      pagination: { pageSize: preferences.pageSize },
      sortingDescending: {
        defaultState: { sortingColumn: columnDefinitions[1] },
      },
      selection: {},
    });

  const alertDismiss = (e) => {
    setIsFilterLoading(false);
    setAnswerMsg("");
  };

  const doSummarize = async () => {
    if (
      !selectedItems ||
      !Array.isArray(selectedItems) ||
      selectedItems.length === 0
    ) {
      alert("请选择要分析的数据");
      return;
    }
    const requestApi = SUMMARIZE_API;
    const requestAnswer = filterProps.filteringText
      ? items.map((i) => i.answers?.substring(0, 2000))
      : selectedItems.map((i) => i.answers?.substring(0, 2000));
    const postData = { answers: requestAnswer, question: query };
    try {
      setIsFilterLoading(true);
      const response = await fetch(requestApi, {
        method: "POST",
        headers: POST_HEADERS,
        body: JSON.stringify(postData),
        signal,
      });
      const data = response.body;
      const reader = data.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let text = "";
      while (!done) {
        if (stopConversationRef.current === true) {
          controller.abort();
          done = true;
          break;
        }
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value);
        text += chunkValue;
        setAnswerMsg(text + "_");
      }
      setAnswerMsg(text);
    } catch (error) {
      console.error("doSummarizeError", error);
    } finally {
      setIsFilterLoading(false);
    }
  };

  const sortData = (event) => {
    if (event.detail.sortingColumn.id === "upload_date") {
      if (isDesc) {
        setNewItems(
          new_items.sort(
            (a, b) =>
              new Date(a[event.detail.sortingColumn.id]) -
              new Date(b[event.detail.sortingColumn.id])
          )
        );
      } else {
        setNewItems(
          new_items.sort(
            (a, b) =>
              new Date(b[event.detail.sortingColumn.id]) -
              new Date(a[event.detail.sortingColumn.id])
          )
        );
      }
    }
    if (isDesc) {
      setNewItems(
        new_items.sort(
          (a, b) =>
            a[event.detail.sortingColumn.id] - b[event.detail.sortingColumn.id]
        )
      );
    } else {
      setNewItems(
        new_items.sort(
          (a, b) =>
            b[event.detail.sortingColumn.id] - a[event.detail.sortingColumn.id]
        )
      );
    }
    setTableSortingField(event.detail.sortingColumn);
    setIsDesc(!isDesc);
  };

  const stopSummarize = () => {
    stopConversationRef.current = true;
    setTimeout(() => {
      stopConversationRef.current = false;
    }, 1000);
  };

  useEffect(() => {
    setSelectedItems(new_items);
  }, [new_items]);

  useEffect(() => {
    if (btnLoading) {
      setAnswerMsg("");
      actions.setFiltering();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [btnLoading]);

  return (
    <SpaceBetween size="l" key="space-table">
      <MainSearchHeader
        setQuery={setQuery}
        setNewItems={setNewItems}
        btnLoading={btnLoading}
        setBtnLoading={setBtnLoading}
        key="main-search-seader"
      />
      <div>
        {answerMsg && (
          <Alert
            key="alt-answer-msg"
            statusIconAriaLabel="Info"
            header="分析结果"
            dismissible
            onDismiss={alertDismiss}
          >
            {answerMsg}
          </Alert>
        )}
      </div>
      <Table
        key="data-table"
        {...collectionProps}
        columnDefinitions={columnDefinitions}
        visibleColumns={preferences.visibleContent}
        items={items}
        selectionType="multi"
        ariaLabels={distributionSelectionLabels}
        stickyHeader
        resizableColumns
        onColumnWidthsChange={saveWidths}
        wrapLines={preferences.wrapLines}
        empty={
          <Box margin={{ vertical: "xs" }} textAlign="center" color="inherit">
            <SpaceBetween size="m">
              <b>No resources</b>
            </SpaceBetween>
          </Box>
        }
        header={
          <FullPageHeader
            selectedItems={collectionProps.selectedItems}
            totalItems={new_items}
          />
        }
        onSelectionChange={({ detail }) => {
          setSelectedItems(detail.selectedItems);
        }}
        selectedItems={selectedItems}
        onSortingChange={(e) => sortData(e)}
        sortingColumn={tableSortingField}
        sortingDescending={isDesc}
        loading={btnLoading}
        filter={
          <>
            <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
              <FormField label="过滤词">
                <TextFilter
                  className="filter-container-text"
                  {...filterProps}
                  filteringAriaLabel="请输入过滤词"
                  filteringPlaceholder="请输入过滤词"
                  countText={getFilterCounterText(filteredItemsCount)}
                />
              </FormField>
              <FormField label="分析操作">
                <div>
                  <Button
                    iconUrl="/icons8-brain-64.png"
                    disabled={!selectedItems || selectedItems.length === 0}
                    loading={isFilterLoading}
                    onClick={doSummarize}
                    variant="primary"
                    className="btn-brain-img"
                  >
                    &nbsp;智&nbsp;能&nbsp;分&nbsp;析
                  </Button>
                  <Button
                    iconName="view-full"
                    disabled={!isFilterLoading}
                    className="stop-filter-btn" // ⏹
                    variant="link"
                    onClick={stopSummarize}
                  >
                    停&nbsp;止&nbsp;分&nbsp;析
                  </Button>
                </div>
              </FormField>
            </Grid>
            <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}></Grid>
          </>
        }
        preferences={
          <Preferences
            preferences={preferences}
            setPreferences={setPreferences}
          />
        }
      />
    </SpaceBetween>
  );
}

function SearchMain({ distributions }) {
  return (
    <CustomAppLayout
      content={<TableContent distributions={distributions} />}
      contentType="table"
      stickyNotifications
      navigationHide
      toolsHide
    />
  );
}

export default SearchMain;
