'use client';

import { useRef, useState } from 'react';
import { Camera, ImagePlus, Trash2 } from 'lucide-react';
import { Button, Input } from '@/components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useDeletePropertyPhoto, useUploadPropertyPhoto } from '@/hooks/use-properties';
import type { PropertyPhoto } from '@/types';

export function PhotoManager({
  propertyId,
  photos,
}: {
  propertyId: string;
  photos: PropertyPhoto[];
}) {
  const uploadPhoto = useUploadPropertyPhoto();
  const deletePhoto = useDeletePropertyPhoto();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [caption, setCaption] = useState('');
  const [isCover, setIsCover] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Choose an image before uploading.');
      return;
    }

    setError(null);

    try {
      await uploadPhoto.mutateAsync({
        propertyId,
        data: {
          file: selectedFile,
          caption: caption || undefined,
          is_cover: isCover,
          position: photos.length,
        },
      });

      setSelectedFile(null);
      setCaption('');
      setIsCover(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch {
      setError('Photo upload failed. Please try again.');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Camera className="h-5 w-5 text-blue-600" />
          Photos
        </CardTitle>
        <CardDescription>
          Upload listing media after the draft is created. Cover photos appear first on public search.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4 rounded-2xl border border-gray-200 bg-gray-50 p-4">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-600 file:mr-4 file:rounded-lg file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-blue-700"
          />
          <Input
            label="Caption"
            value={caption}
            onChange={(event) => setCaption(event.target.value)}
            placeholder="Bright living room with balcony view"
          />
          <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={isCover}
              onChange={(event) => setIsCover(event.target.checked)}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Use as cover photo
          </label>
          {error ? (
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}
          <Button type="button" onClick={handleUpload} isLoading={uploadPhoto.isPending}>
            <ImagePlus className="mr-2 h-4 w-4" />
            Upload photo
          </Button>
        </div>

        {photos.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {photos.map((photo) => (
              <div key={photo.id} className="overflow-hidden rounded-2xl border border-gray-200">
                <div className="relative aspect-[4/3] bg-gray-100">
                  <img src={photo.url} alt={photo.caption ?? 'Property photo'} className="h-full w-full object-cover" />
                  {photo.is_cover ? (
                    <span className="absolute left-3 top-3 rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">
                      Cover
                    </span>
                  ) : null}
                </div>
                <div className="flex items-start justify-between gap-3 p-4">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{photo.caption || 'Untitled photo'}</p>
                    <p className="mt-1 text-xs text-gray-400">Position {photo.position ?? 0}</p>
                  </div>
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      if (confirm('Remove this photo from the listing?')) {
                        deletePhoto.mutate({ propertyId, photoId: photo.id });
                      }
                    }}
                    isLoading={deletePhoto.isPending}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center">
            <p className="text-sm text-gray-500">
              No photos uploaded yet. Add a few strong visuals before publishing the listing.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
