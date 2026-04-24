/**
 * SEINENTAI4US — Social Share Buttons (react-share)
 */
import {
  TwitterShareButton,
  LinkedinShareButton,
  WhatsappShareButton,
  TwitterIcon,
  LinkedinIcon,
  WhatsappIcon,
} from 'react-share';
import { cn } from '@/lib/utils';

interface SocialShareButtonsProps {
  url: string;
  title: string;
  className?: string;
}

export default function SocialShareButtons({ url, title, className }: SocialShareButtonsProps) {
  const iconSize = 40;

  return (
    <div className={cn("flex justify-around items-center gap-2 p-1", className)}>
      <TwitterShareButton url={url} title={title} className="focus:outline-none outline-none">
        <div className="group flex flex-col items-center gap-2 transition-all duration-300 hover:-translate-y-1">
          <div className="rounded-full shadow-sm group-hover:shadow-md transition-all duration-300 overflow-hidden ring-2 ring-transparent group-hover:ring-blue-100">
            <TwitterIcon size={iconSize} round={true} />
          </div>
          <span className="text-[10px] font-medium text-slate-400 group-hover:text-blue-500 transition-colors">Twitter</span>
        </div>
      </TwitterShareButton>

      <LinkedinShareButton url={url} title={title} className="focus:outline-none outline-none">
        <div className="group flex flex-col items-center gap-2 transition-all duration-300 hover:-translate-y-1">
          <div className="rounded-full shadow-sm group-hover:shadow-md transition-all duration-300 overflow-hidden ring-2 ring-transparent group-hover:ring-blue-200">
            <LinkedinIcon size={iconSize} round={true} />
          </div>
          <span className="text-[10px] font-medium text-slate-400 group-hover:text-blue-700 transition-colors">LinkedIn</span>
        </div>
      </LinkedinShareButton>

      <WhatsappShareButton url={url} title={title} separator=" :: " className="focus:outline-none outline-none">
        <div className="group flex flex-col items-center gap-2 transition-all duration-300 hover:-translate-y-1">
          <div className="rounded-full shadow-sm group-hover:shadow-md transition-all duration-300 overflow-hidden ring-2 ring-transparent group-hover:ring-green-100">
            <WhatsappIcon size={iconSize} round={true} />
          </div>
          <span className="text-[10px] font-medium text-slate-400 group-hover:text-green-500 transition-colors">WhatsApp</span>
        </div>
      </WhatsappShareButton>
    </div>
  );
}
