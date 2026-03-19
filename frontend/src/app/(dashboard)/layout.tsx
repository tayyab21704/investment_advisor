import Header from '@/components/layout/Header';
import LeftSidebar from '@/components/layout/LeftSidebar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden bg-bg-base">
      <LeftSidebar />
      <div className="flex-1 flex flex-col relative overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto no-scrollbar pt-[80px]">
          {children}
        </main>
      </div>
    </div>
  );
}
