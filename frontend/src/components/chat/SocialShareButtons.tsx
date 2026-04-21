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
  const iconSize = 32;
  const borderRadius = 8;

  return (
    <div className={cn("flex items-center gap-3 p-2", className)}>
      <TwitterShareButton url={url} title={title}>
        <div className="group flex flex-col items-center gap-1">
          <TwitterIcon size={iconSize} round={false} borderRadius={borderRadius} />
          <span className="text-[10px] font-medium text-slate-500 group-hover:text-blue-400">Twitter</span>
        </div>
      </TwitterShareButton>

      <LinkedinShareButton url={url} title={title}>
        <div className="group flex flex-col items-center gap-1">
          <LinkedinIcon size={iconSize} round={false} borderRadius={borderRadius} />
          <span className="text-[10px] font-medium text-slate-500 group-hover:text-blue-700">LinkedIn</span>
        </div>
      </LinkedinShareButton>

      <WhatsappShareButton url={url} title={title} separator=" :: ">
        <div className="group flex flex-col items-center gap-1">
          <WhatsappIcon size={iconSize} round={false} borderRadius={borderRadius} />
          <span className="text-[10px] font-medium text-slate-500 group-hover:text-green-500">WhatsApp</span>
        </div>
      </WhatsappShareButton>
    </div>
  );
}
