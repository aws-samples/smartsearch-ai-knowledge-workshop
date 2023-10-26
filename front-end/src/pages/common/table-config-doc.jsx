// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React from "react";
import { CollectionPreferences } from "@cloudscape-design/components";

const VISIBLE_CONTENT_OPTIONS = [
  {
    label: "可展示的列",
    options: [
      { id: "id", label: "ID" },
      { id: "question", label: "问题" },
      { id: "answers", label: "分析与处理" },
      { id: "machinetypename", label: "工艺名称" },
      { id: "linename", label: "流水线" },
      { id: "manufacturing_process_number", label: "工艺号" },
      { id: "reply_upload_file", label: "相关手册" },
      { id: "action_des", label: "处理方式" },
      { id: "root_cause_des", label: "根本原因" },
      { id: "upload_date", label: "更新日期" },
      { id: "problemid", label: "问题ID" },
      { id: "linekey", label: "流水线ID" },
      { id: "machinekey", label: "设备ID" },
      { id: "action_linkid", label: "处理方式Id" },
      { id: "root_causeid", label: "根本原因ID" },
      { id: "machinetypekey", label: "工艺号ID" },
    ],
  },
];

export const PAGE_SIZE_OPTIONS = [
  { value: 10, label: "10 Distributions" },
  { value: 30, label: "30 Distributions" },
  { value: 50, label: "50 Distributions" },
];

export const DEFAULT_PREFERENCES = {
  pageSize: 50,
  visibleContent: [
    "question",
    "answers",
    "machinetypename",
    "linename",
    "manufacturing_process_number",
    "reply_upload_file",
    "upload_date",
    "problemid",
  ],
  wrapLines: true,
};

export const Preferences = ({
  preferences,
  setPreferences,
  disabled,
  pageSizeOptions = PAGE_SIZE_OPTIONS,
  visibleContentOptions = VISIBLE_CONTENT_OPTIONS,
}) => (
  <CollectionPreferences
    title="页面设置"
    confirmLabel="确认"
    cancelLabel="取消"
    disabled={disabled}
    preferences={preferences}
    onConfirm={({ detail }) => setPreferences(detail)}
    wrapLinesPreference={{
      label: "换行展示",
      description: "开启后超宽的内容换行展示，默认隐藏超长内容部分。",
    }}
    visibleContentPreference={{
      title: "展示列",
      options: visibleContentOptions,
    }}
  />
);
