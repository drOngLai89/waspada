export type ReportCategory =
  | 'Bullying' | 'Cyberbullying' | 'Physical Violence' | 'Verbal Harassment'
  | 'Discrimination' | 'Vandalism' | 'Theft' | 'Other';

export type ReportItem = {
  id: string;
  category: ReportCategory;
  dateISO: string;
  timeISO: string;
  locationText: string;
  description: string;
  photoUris: string[];
  aiReport: string;
  createdAt: number;
};
