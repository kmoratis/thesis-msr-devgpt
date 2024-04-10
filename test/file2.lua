-- Instantiate Reaper API
local reaper = reaper

function main()
    -- Get the active MIDI editor
    local editor = reaper.MIDIEditor_GetActive()
    if editor == nil then return end

    -- Get the current take being edited
    local take = reaper.MIDIEditor_GetTake(editor)
    if take == nil then return end

    -- Get the number of MIDI events in the take
    local _, count = reaper.MIDI_CountEvts(take)
    
    -- Iterate over all MIDI events
    for i = 0, count - 1 do
        local retval, selected, muted, startppqpos, chanmsg, chan, msg2, msg3, text = reaper.MIDI_GetTextSysexEvt(take, i)

        -- Check if the event is a lyric event (0x05) and selected
        if selected and chanmsg == 0x05 then
            -- Append a '#' to the text if text is not nil
            if text ~= nil then
                text = text .. '#'
            else
                text = '#'
            end

            -- Set the modified event back
            reaper.MIDI_SetTextSysexEvt(take, i, selected, muted, startppqpos, chanmsg, chan, msg2, msg3, text)
        end
    end
end

main()
