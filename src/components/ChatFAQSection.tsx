import { Card } from "./ui/card";

interface ChatFAQSectionProps {
  onQuestionClick: (question: string) => void;
}

export function ChatFAQSection({ onQuestionClick }: ChatFAQSectionProps) {
  const topicCards = [
    {
      id: "ai-translation",
      label: "AI 轉譯",
      image: "/images/AI轉譯image.jpg",
      question: "我想了解 AI 轉譯服務，可以幫助我做什麼？"
    },
    {
      id: "healing-space",
      label: "痊癒空間",
      image: "/images/痊癒空間image.jpg",
      question: "請介紹一下痊癒空間的服務內容"
    },
    {
      id: "light-politics",
      label: "輕參政",
      image: "/images/輕參政image.jpg",
      question: "什麼是輕參政？青年可以如何參與？"
    },
    {
      id: "youth-exchange",
      label: "青年交流",
      image: "/images/青年在咖啡館交流image.jpg",
      question: "有哪些青年交流的活動可以參加？"
    }
  ];

  return (
    <Card className="p-4 border bg-[#F8F6F3] border-[#E8E4DE]">
      <h4 className="text-[16px] font-medium mb-3 text-foreground select-text cursor-text">
        熱門主題快速選單
      </h4>
      <div className="grid grid-cols-2 gap-3">
        {topicCards.map((topic) => (
          <button
            key={topic.id}
            className="group relative overflow-hidden rounded-lg border border-[#E8E4DE] bg-white hover:border-[#5B8C5A] hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#5B8C5A] focus:ring-offset-2"
            onClick={() => onQuestionClick(topic.question)}
          >
            <div className="aspect-[4/3] overflow-hidden">
              <img
                src={topic.image}
                alt={topic.label}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
              />
            </div>
            <div className="p-2 text-center">
              <span className="text-[13px] font-medium text-[#3A3A3A] group-hover:text-[#5B8C5A] select-text cursor-text">
                {topic.label}
              </span>
            </div>
          </button>
        ))}
      </div>
    </Card>
  );
}
