import { TableHeader } from "../common/common-components";

const FullPageHeader = ({ resourceName = "Result", ...props }) => {
  return <TableHeader title={resourceName} {...props} />;
};
export default FullPageHeader;
