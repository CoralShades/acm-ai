'use client'

import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { useCreateACMRecord, useUpdateACMRecord } from '@/lib/hooks/use-acm'
import type { ACMRecord, ACMRecordCreateRequest, ACMRecordUpdateRequest } from '@/lib/types/acm'
import { useFieldSchema } from '@/lib/hooks/useACMItems'
import { DependentPicklistEditor } from './DependentPicklistEditor'

// Schema keeps everything as strings - conversion happens in onSubmit
const acmRecordSchema = z.object({
  school_name: z.string().min(1, 'School name is required'),
  school_code: z.string().optional(),
  building_id: z.string().min(1, 'Building ID is required'),
  building_name: z.string().optional(),
  building_year: z.string().optional(),
  building_construction: z.string().optional(),
  room_id: z.string().optional(),
  room_name: z.string().optional(),
  room_area: z.string().optional(),
  area_type: z.string().optional(),
  product: z.string().min(1, 'Product is required'),
  material_description: z.string().min(1, 'Material description is required'),
  extent: z.string().optional(),
  location: z.string().optional(),
  friable: z.string().optional(),
  acm_product_group: z.string().optional(),
  acm_product_type: z.string().optional(),
  building_type: z.string().optional(),
  material_condition: z.string().optional(),
  risk_status: z.string().optional(),
  result: z.string().min(1, 'Result is required'),
  page_number: z.string().optional(),
})

type ACMRecordFormData = z.infer<typeof acmRecordSchema>

interface ACMRecordDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceId: string
  record?: ACMRecord | null
  mode: 'create' | 'edit'
}

export function ACMRecordDialog({
  open,
  onOpenChange,
  sourceId,
  record,
  mode,
}: ACMRecordDialogProps) {
  const createRecord = useCreateACMRecord()
  const updateRecord = useUpdateACMRecord()
  const { data: fieldSchema } = useFieldSchema()

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    reset,
    setValue,
    watch,
  } = useForm<ACMRecordFormData>({
    resolver: zodResolver(acmRecordSchema),
    mode: 'onChange',
    defaultValues: {
      school_name: '',
      school_code: '',
      building_id: '',
      building_name: '',
      building_year: '',
      building_construction: '',
      room_id: '',
      room_name: '',
      room_area: '',
      area_type: '',
      product: '',
      material_description: '',
      extent: '',
      location: '',
      friable: '',
      acm_product_group: '',
      acm_product_type: '',
      building_type: '',
      material_condition: '',
      risk_status: '',
      result: '',
      page_number: '',
    },
  })

  // Load record data when editing
  useEffect(() => {
    if (open && mode === 'edit' && record) {
      reset({
        school_name: record.school_name || '',
        school_code: record.school_code || '',
        building_id: record.building_id || '',
        building_name: record.building_name || '',
        building_year: record.building_year?.toString() || '',
        building_construction: record.building_construction || '',
        room_id: record.room_id || '',
        room_name: record.room_name || '',
        room_area: record.room_area?.toString() || '',
        area_type: record.area_type || '',
        product: record.product || '',
        material_description: record.material_description || '',
        extent: record.extent || '',
        location: record.location || '',
        friable: record.friable || '',
        acm_product_group: record.acm_product_group || '',
        acm_product_type: record.acm_product_type || '',
        building_type: record.building_type || '',
        material_condition: record.material_condition || '',
        risk_status: record.risk_status || '',
        result: record.result || '',
        page_number: record.page_number?.toString() || '',
      })
    } else if (open && mode === 'create') {
      reset()
    }
  }, [open, mode, record, reset])

  // Build partial ACMRecord from watched form values — used by DependentPicklistEditor (AC6)
  const watchedForPicker = watch(['friable', 'acm_product_group', 'building_type'])
  const formRowData = useMemo<Partial<ACMRecord>>(() => ({
    friable: watchedForPicker[0] || undefined,
    acm_product_group: watchedForPicker[1] || undefined,
    building_type: watchedForPicker[2] || undefined,
  }), [watchedForPicker[0], watchedForPicker[1], watchedForPicker[2]])

  const closeDialog = () => {
    onOpenChange(false)
    reset()
  }

  const onSubmit = async (data: ACMRecordFormData) => {
    // Helper to parse optional integers from string fields
    const parseOptionalInt = (val?: string): number | undefined => {
      if (!val || val === '') return undefined
      const parsed = parseInt(val, 10)
      return isNaN(parsed) ? undefined : parsed
    }

    // Helper to parse optional floats from string fields
    const parseOptionalFloat = (val?: string): number | undefined => {
      if (!val || val === '') return undefined
      const parsed = parseFloat(val)
      return isNaN(parsed) ? undefined : parsed
    }

    if (mode === 'create') {
      const createData: ACMRecordCreateRequest = {
        source_id: sourceId,
        school_name: data.school_name,
        building_id: data.building_id,
        product: data.product,
        material_description: data.material_description,
        result: data.result,
        ...(data.school_code && { school_code: data.school_code }),
        ...(data.building_name && { building_name: data.building_name }),
        ...(parseOptionalInt(data.building_year) !== undefined && { building_year: parseOptionalInt(data.building_year) }),
        ...(data.building_construction && { building_construction: data.building_construction }),
        ...(data.room_id && { room_id: data.room_id }),
        ...(data.room_name && { room_name: data.room_name }),
        ...(parseOptionalFloat(data.room_area) !== undefined && { room_area: parseOptionalFloat(data.room_area) }),
        ...(data.area_type && { area_type: data.area_type }),
        ...(data.extent && { extent: data.extent }),
        ...(data.location && { location: data.location }),
        ...(data.friable && { friable: data.friable }),
        ...(data.acm_product_group && { acm_product_group: data.acm_product_group }),
        ...(data.acm_product_type && { acm_product_type: data.acm_product_type }),
        ...(data.building_type && { building_type: data.building_type }),
        ...(data.material_condition && { material_condition: data.material_condition }),
        ...(data.risk_status && { risk_status: data.risk_status }),
        ...(parseOptionalInt(data.page_number) !== undefined && { page_number: parseOptionalInt(data.page_number) }),
      }
      await createRecord.mutateAsync(createData)
    } else if (record) {
      const updateData: ACMRecordUpdateRequest = {
        school_name: data.school_name,
        building_id: data.building_id,
        product: data.product,
        material_description: data.material_description,
        result: data.result,
        school_code: data.school_code || undefined,
        building_name: data.building_name || undefined,
        building_year: parseOptionalInt(data.building_year),
        building_construction: data.building_construction || undefined,
        room_id: data.room_id || undefined,
        room_name: data.room_name || undefined,
        room_area: parseOptionalFloat(data.room_area),
        area_type: data.area_type || undefined,
        extent: data.extent || undefined,
        location: data.location || undefined,
        friable: data.friable || undefined,
        acm_product_group: data.acm_product_group || undefined,
        acm_product_type: data.acm_product_type || undefined,
        building_type: data.building_type || undefined,
        material_condition: data.material_condition || undefined,
        risk_status: data.risk_status || undefined,
        page_number: parseOptionalInt(data.page_number),
      }
      await updateRecord.mutateAsync({
        recordId: record.id,
        sourceId: sourceId,
        data: updateData,
      })
    }
    closeDialog()
  }

  const isPending = createRecord.isPending || updateRecord.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>
            {mode === 'create' ? 'Add ACM Record' : 'Edit ACM Record'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'create'
              ? 'Add a new ACM (Asbestos Containing Material) record.'
              : 'Update the ACM record details.'}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh] pr-4">
          <form id="acm-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* School Information */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">School Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="school_name">School Name *</Label>
                  <Input
                    id="school_name"
                    {...register('school_name')}
                    placeholder="Enter school name"
                  />
                  {errors.school_name && (
                    <p className="text-sm text-destructive">{errors.school_name.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="school_code">School Code</Label>
                  <Input
                    id="school_code"
                    {...register('school_code')}
                    placeholder="e.g., 1124"
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Building Information */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">Building Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="building_id">Building ID *</Label>
                  <Input
                    id="building_id"
                    {...register('building_id')}
                    placeholder="e.g., B00A"
                  />
                  {errors.building_id && (
                    <p className="text-sm text-destructive">{errors.building_id.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="building_name">Building Name</Label>
                  <Input
                    id="building_name"
                    {...register('building_name')}
                    placeholder="e.g., Admin Block"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="building_year">Year Built</Label>
                  <Input
                    id="building_year"
                    type="number"
                    {...register('building_year')}
                    placeholder="e.g., 1965"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="building_type">Building Type</Label>
                  {fieldSchema ? (
                    <DependentPicklistEditor
                      mode="form"
                      fieldApiName="Building_Type__c"
                      schema={fieldSchema}
                      rowData={formRowData}
                      value={watch('building_type') || ''}
                      onChange={(val) => setValue('building_type', val)}
                      placeholder="Select building type"
                      id="building_type"
                      className="border border-input rounded-md px-3 py-2"
                    />
                  ) : (
                    <Input
                      id="building_type"
                      {...register('building_type')}
                      placeholder="e.g., School"
                    />
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="building_construction">Construction Category</Label>
                  {fieldSchema ? (
                    <DependentPicklistEditor
                      mode="form"
                      fieldApiName="Building_Category__c"
                      schema={fieldSchema}
                      rowData={formRowData}
                      value={watch('building_construction') || ''}
                      onChange={(val) => setValue('building_construction', val)}
                      placeholder="Select category"
                      id="building_construction"
                      className="border border-input rounded-md px-3 py-2"
                    />
                  ) : (
                    <Input
                      id="building_construction"
                      {...register('building_construction')}
                      placeholder="e.g., Brick"
                    />
                  )}
                </div>
              </div>
            </div>

            <Separator />

            {/* Room Information */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">Room Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="room_id">Room ID</Label>
                  <Input
                    id="room_id"
                    {...register('room_id')}
                    placeholder="e.g., R0001"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="room_name">Room Name</Label>
                  <Input
                    id="room_name"
                    {...register('room_name')}
                    placeholder="e.g., Main Office"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="room_area">Area (m²)</Label>
                  <Input
                    id="room_area"
                    type="number"
                    step="0.1"
                    {...register('room_area')}
                    placeholder="e.g., 45.5"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="area_type">Area Type</Label>
                  <Select
                    value={watch('area_type') || ''}
                    onValueChange={(value) => setValue('area_type', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select area type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Interior">Interior</SelectItem>
                      <SelectItem value="Exterior">Exterior</SelectItem>
                      <SelectItem value="Grounds">Grounds</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            <Separator />

            {/* ACM Details */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">ACM Details</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="product">Product *</Label>
                  <Input
                    id="product"
                    {...register('product')}
                    placeholder="e.g., Floor Tiles"
                  />
                  {errors.product && (
                    <p className="text-sm text-destructive">{errors.product.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="material_description">Material Description *</Label>
                  <Input
                    id="material_description"
                    {...register('material_description')}
                    placeholder="e.g., Vinyl asbestos tiles"
                  />
                  {errors.material_description && (
                    <p className="text-sm text-destructive">{errors.material_description.message}</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="extent">Extent</Label>
                  <Input
                    id="extent"
                    {...register('extent')}
                    placeholder="e.g., 50m²"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location">Location</Label>
                  <Input
                    id="location"
                    {...register('location')}
                    placeholder="e.g., Floor"
                  />
                </div>
              </div>
            </div>

            <Separator />

            {/* Assessment */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">Assessment</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="friable">Friable</Label>
                  {fieldSchema ? (
                    <DependentPicklistEditor
                      mode="form"
                      fieldApiName="Friability_of_Material__c"
                      schema={fieldSchema}
                      rowData={formRowData}
                      value={watch('friable') || ''}
                      onChange={(val) => setValue('friable', val)}
                      placeholder="Select friability"
                      id="friable"
                      className="border border-input rounded-md px-3 py-2"
                    />
                  ) : (
                    <Select
                      value={watch('friable') || ''}
                      onValueChange={(value) => setValue('friable', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select friability" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Friable">Friable</SelectItem>
                        <SelectItem value="Non Friable">Non Friable</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="acm_product_group">ACM Classification</Label>
                  {fieldSchema ? (
                    <DependentPicklistEditor
                      mode="form"
                      fieldApiName="ACM_Classification__c"
                      schema={fieldSchema}
                      rowData={formRowData}
                      value={watch('acm_product_group') || ''}
                      onChange={(val) => setValue('acm_product_group', val)}
                      placeholder="Select classification"
                      id="acm_product_group"
                      className="border border-input rounded-md px-3 py-2"
                    />
                  ) : (
                    <Select
                      value={watch('acm_product_group') || ''}
                      onValueChange={(value) => setValue('acm_product_group', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select classification" />
                      </SelectTrigger>
                      <SelectContent />
                    </Select>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="acm_product_type">ACM Sub-Classification</Label>
                  {fieldSchema ? (
                    <DependentPicklistEditor
                      mode="form"
                      fieldApiName="ACM_Sub_Classification__c"
                      schema={fieldSchema}
                      rowData={formRowData}
                      value={watch('acm_product_type') || ''}
                      onChange={(val) => setValue('acm_product_type', val)}
                      placeholder="Select sub-classification"
                      id="acm_product_type"
                      className="border border-input rounded-md px-3 py-2"
                    />
                  ) : (
                    <Select
                      value={watch('acm_product_type') || ''}
                      onValueChange={(value) => setValue('acm_product_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select sub-classification" />
                      </SelectTrigger>
                      <SelectContent />
                    </Select>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="material_condition">Condition</Label>
                  <Select
                    value={watch('material_condition') || ''}
                    onValueChange={(value) => setValue('material_condition', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select condition" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Good">Good</SelectItem>
                      <SelectItem value="Fair">Fair</SelectItem>
                      <SelectItem value="Poor">Poor</SelectItem>
                      <SelectItem value="Damaged">Damaged</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="risk_status">Risk Status</Label>
                  <Select
                    value={watch('risk_status') || ''}
                    onValueChange={(value) => setValue('risk_status', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select risk level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Low">Low</SelectItem>
                      <SelectItem value="Medium">Medium</SelectItem>
                      <SelectItem value="High">High</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="result">Result *</Label>
                  <Select
                    value={watch('result') || ''}
                    onValueChange={(value) => setValue('result', value, { shouldValidate: true })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select result" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Positive">Positive</SelectItem>
                      <SelectItem value="Assumed Positive">Assumed Positive</SelectItem>
                      <SelectItem value="Negative">Negative</SelectItem>
                      <SelectItem value="Assumed Negative">Assumed Negative</SelectItem>
                      <SelectItem value="Unknown">Unknown</SelectItem>
                    </SelectContent>
                  </Select>
                  {errors.result && (
                    <p className="text-sm text-destructive">{errors.result.message}</p>
                  )}
                </div>
              </div>
            </div>

            <Separator />

            {/* Reference */}
            <div className="space-y-4">
              <h3 className="text-sm font-semibold">Reference</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="page_number">Page Number</Label>
                  <Input
                    id="page_number"
                    type="number"
                    {...register('page_number')}
                    placeholder="Source document page"
                  />
                </div>
              </div>
            </div>
          </form>
        </ScrollArea>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button type="button" variant="outline" onClick={closeDialog}>
            Cancel
          </Button>
          <Button type="submit" form="acm-form" disabled={!isValid || isPending}>
            {isPending
              ? mode === 'create'
                ? 'Creating...'
                : 'Saving...'
              : mode === 'create'
              ? 'Create Record'
              : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
