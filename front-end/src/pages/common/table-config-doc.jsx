// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0
import React from "react";
import { CollectionPreferences } from "@cloudscape-design/components";

const VISIBLE_CONTENT_OPTIONS = [
  {
    label: "Displayable columns",
    options: [
      { id: "id", label: "ID" },
      { id: "question", label: "Question" },
      { id: "answers", label: "Answers" },
      { id: "upload_date", label: "Update time" },
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
  visibleContent: ["question", "answers"],
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
    title="Page settings"
    confirmLabel="Confirm"
    cancelLabel="Cancel"
    disabled={disabled}
    preferences={preferences}
    onConfirm={({ detail }) => setPreferences(detail)}
    wrapLinesPreference={{
      label: "Line break display",
      description:
        "When enabled, extra-wide content will be displayed in new lines, and extra-long content will be hidden by default.",
    }}
    visibleContentPreference={{
      title: "Display column",
      options: visibleContentOptions,
    }}
  />
);
