import Layout from "@/layouts/admin/Layout";

export interface AleivaLayoutProps {
  children: React.ReactNode;
}

export default async function AleivaLayout({ children }: AleivaLayoutProps) {
  return await Layout({ children });
}
